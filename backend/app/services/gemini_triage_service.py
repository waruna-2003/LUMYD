"""
LUMYD Gemini Triage Service
Uses Google Gemini (gemini-3.6-flash) as an automated analytical oracle to resolve
ambiguous, novel, or low-confidence queries that cannot be routed locally.
Enforces Free Tier quota limits and rate-limiting via GeminiQuotaGuard.
"""

import json
import os
from typing import Any, Dict, List, Optional

from app.core.quota_guard import quota_guard

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GeminiTriageService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key) if (GENAI_AVAILABLE and self.api_key) else None
        self.model_name = "gemini-3.6-flash"

    def is_available(self) -> bool:
        """Returns True if SDK is installed, API key is set, and daily quota is available."""
        if not self.client:
            return False
        can_req, _ = quota_guard.can_request()
        return can_req

    def resolve_ambiguous_query(
        self,
        query: str,
        available_metrics: List[str],
        available_dimensions: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Uses Gemini to extract structured intent and slots for an ambiguous or novel query.
        Returns None if the query is non-analytical / out-of-scope or if API quota is reached.
        """
        # 1. Check response cache first (0 API cost)
        cached = quota_guard.get_cached_response(query)
        if cached:
            print(f"[*] Cache hit for query: '{query}' (0 API requests consumed)")
            return cached

        # 2. Check quota availability
        if not self.is_available():
            print("[!] Gemini Triage is unavailable or daily quota limit reached.")
            return None

        # 3. Throttle request to honor <= 15 RPM
        quota_guard.throttle_and_record()

        prompt = f"""
You are the LUMYD Business Intelligence Query Parser.
A user has asked a question against a business dataset. The query may be in formal English, casual English with typos/slang, or code-mixed Singlish (Sinhala transliterated into English letters with English business terms).

Dataset Context:
- Available Metrics: {available_metrics}
- Available Dimensions: {available_dimensions}

User Query: "{query}"

Determine whether this query is a genuine analytical question that can be answered by the dataset, or if it is out-of-scope (e.g., weather, chit-chat, general trivia, unrelated tasks).

If the query is OUT-OF-SCOPE or unrelated to data analysis:
Return:
{{
  "is_applicable": false,
  "reason": "Query is not related to dataset analysis"
}}

If the query IS APPLICABLE to business analysis:
Map it into one of the allowed intents:
- "root_cause": why a metric changed, dropped, rose, or deviated
- "ranking": top or bottom performing entities, products, branches
- "comparison": comparing metric across groups, categories, or channels
- "trend": metric movement over time (daily, monthly, quarterly)
- "distribution": statistical spread, dispersion, frequency

Select the closest matching metric from Available Metrics and dimensions from Available Dimensions.
Return valid JSON matching this exact structure:
{{
  "is_applicable": true,
  "intent": "root_cause | ranking | comparison | trend | distribution",
  "target_metric": "<chosen metric from Available Metrics>",
  "dimensions": ["<chosen dimension from Available Dimensions>"],
  "filters": {{}},
  "time_period": "<e.g. last_month, q3, or null>",
  "granularity": "day | week | month | quarter | year"
}}
"""

        try:
            print(f"[*] Calling Gemini Triage ({self.model_name}) for query: '{query}'...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )

            result = json.loads(response.text)
            if not result.get("is_applicable", False):
                print(f"    [!] Gemini determined query is out-of-scope: {result.get('reason')}")
                return None

            intent = result.get("intent")
            target_metric = result.get("target_metric")

            # Validate extracted metric exists in available metrics
            if target_metric not in available_metrics and available_metrics:
                target_metric = available_metrics[0]
                result["target_metric"] = target_metric

            valid_intents = {"root_cause", "ranking", "comparison", "trend", "distribution"}
            if intent not in valid_intents:
                intent = "trend"
                result["intent"] = intent

            parsed_structure = {
                "intent": intent,
                "target_metric": target_metric,
                "dimensions": [d for d in result.get("dimensions", []) if d in available_dimensions],
                "filters": result.get("filters", {}),
                "time_period": result.get("time_period"),
                "granularity": result.get("granularity", "month")
            }

            # Cache the successful extraction
            quota_guard.cache_response(query, parsed_structure)
            print(f"    [+] Gemini successfully triaged query -> intent: '{intent}', metric: '{target_metric}'")
            return parsed_structure

        except Exception as e:
            print(f"    [!] Gemini Triage call failed: {e}")
            return None


# Singleton instance
gemini_triage = GeminiTriageService()
