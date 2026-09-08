"""LUMYD Gemini Code Teacher Service

Uses Google Gemini (gemini-3.6-flash) as an expert coding teacher.
When the local predefined library does not know how to handle a query,
Gemini writes custom, executable Python (Pandas) code and produces a
human-readable explanation in English, Singlish, or Sinhala.
Strictly guarded by GeminiQuotaGuard (<= 15 RPM, <= 1,000 requests/day).
"""

import json
import os
import re
from typing import Any, Dict, List, Optional
import pandas as pd

from app.core.quota_guard import quota_guard
from app.services.narrative_generator import MultilingualNarrativeGenerator

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GeminiCodeTeacher:
    """The Master Teacher: Generates Python code and multilingual explanations

    for novel, complex, or colloquial queries.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = (
            genai.Client(api_key=self.api_key)
            if (GENAI_AVAILABLE and self.api_key)
            else None
        )
        self.model_name = "gemini-3.6-flash"

    def is_available(self) -> bool:
        """Returns True if SDK is ready and daily quota is within budget."""
        if not self.client and GENAI_AVAILABLE:
            from dotenv import load_dotenv
            load_dotenv()
            self.api_key = os.getenv("GEMINI_API_KEY")
            if self.api_key:
                self.client = genai.Client(api_key=self.api_key)

        if not self.client:
            return False
        can_req, _ = quota_guard.can_request()
        return can_req

    @staticmethod
    def get_schema_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """Summarizes dataframe schema, column types, and sample categorical values."""
        summary = {}
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            if pd.api.types.is_numeric_dtype(df[col]):
                summary[col] = {
                    "type": "numeric",
                    "min": float(df[col].min()) if not df[col].empty and not pd.isna(df[col].min()) else None,
                    "max": float(df[col].max()) if not df[col].empty and not pd.isna(df[col].max()) else None,
                }
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                summary[col] = {"type": "datetime"}
            else:
                sample_vals = [str(x) for x in df[col].dropna().unique()[:6]]
                summary[col] = {
                    "type": "categorical",
                    "sample_values": sample_vals,
                    "unique_count": int(df[col].nunique()),
                }
        return summary

    def teach_code(
        self,
        query: str,
        df: pd.DataFrame,
        detected_language: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Invokes Gemini to understand the query, write Python code on `df`, and

        generate a human-readable explanation.
        """
        # 1. Check local query cache first (0 API requests consumed)
        cached = quota_guard.get_cached_response(f"code_teacher::{query}")
        if cached:
            print(f"[*] Cache hit for code teacher query: '{query}' (0 API calls)")
            return cached

        # 2. Check quota availability
        if not self.is_available():
            print("[!] Gemini Code Teacher is unavailable or daily quota ceiling reached.")
            return None

        # 3. Throttle request to strictly guarantee <= 15 RPM
        quota_guard.throttle_and_record()

        lang = detected_language or MultilingualNarrativeGenerator.detect_language(query)
        schema_info = self.get_schema_summary(df)
        sample_records = df.head(2).to_dict(orient="records")

        lang_instruction = {
            "singlish": "The user is asking in Singlish (colloquial Sri Lankan English mixed with Sinhala words like 'adu', 'wedi', 'ai mcn', 'kiyada', 'balanna'). Your human_explanation MUST be in authentic, friendly Singlish.",
            "sinhala": "The user is asking in Sinhala (සිංහල). Your human_explanation MUST be in fluent, professional Sinhala Unicode.",
            "english": "The user is asking in English. Your human_explanation MUST be in clear, professional business English.",
        }.get(lang, "Respond in the language of the user query.")

        prompt = f"""You are the Master Data Science & Python Teacher for LUMYD Business Intelligence.
Your job is to understand the user's business query, write self-contained Python code to compute the exact answer from a pandas DataFrame `df`, and provide a clear, friendly human explanation.

Dataset Schema Context:
Columns and Types:
{json.dumps(schema_info, indent=2)}

Sample Rows from df:
{json.dumps(sample_records, indent=2, default=str)}

User Query: "{query}"
Detected Dialect: {lang}
Dialect Guideline: {lang_instruction}

STRICT CODING RULES:
1. The DataFrame is already loaded in memory as variable `df`.
2. Write clean Python code that computes the answer and assigns it to a variable named `result`.
3. `result` can be:
   - A single number/string (e.g. `result = 45000` or `result = 'Product A'`)
   - A summary dictionary (e.g. `result = {{'metric': '...', 'value': ...}}`)
   - A aggregated DataFrame or Series (e.g. `result = df.groupby('Region')['Sales_Amount'].sum()`)
4. Only use `pandas as pd`, `numpy as np`, `datetime`, and `math`. Do NOT import any other libraries.
5. Be resilient to case sensitivity: use `.str.lower()` or `.astype(str)` when filtering string columns.
6. If the query asks for 'profit' but no 'Profit' column exists, calculate profit if 'Unit_Cost' and 'Sales_Amount' exist (e.g. `df['Sales_Amount'] - df['Unit_Cost'] * df.get('Quantity_Sold', 1)`), or use the closest available financial metric.

OUTPUT FORMAT:
You MUST return ONLY a valid JSON object with this exact structure:
{{
  "intent_label": "short_snake_case_label (e.g. product_profit_lookup, region_comparison, sales_trend)",
  "python_code": "# python code here\\nresult = ...",
  "human_explanation": "Clear, friendly, human-readable answer directly addressing what the user asked in the requested dialect.",
  "is_out_of_scope": false
}}

If the query is completely unrelated to data analysis or cannot be answered with this dataset, set:
{{
  "intent_label": "out_of_scope",
  "python_code": "",
  "human_explanation": "Polite explanation that this question is outside the scope of the dataset.",
  "is_out_of_scope": true
}}
"""

        print(f"[*] Calling Gemini Code Teacher ({self.model_name}) for query: '{query}'...")
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )

            raw_text = response.text.strip()
            # Clean possible markdown wrapping
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            parsed = json.loads(raw_text.strip())

            if parsed.get("is_out_of_scope"):
                print(f"    [!] Gemini determined query is out-of-scope: {parsed.get('human_explanation')}")
                return None

            result_payload = {
                "intent_label": parsed.get("intent_label", "custom_analytical_task"),
                "python_code": parsed.get("python_code", ""),
                "human_explanation": parsed.get("human_explanation", ""),
                "language": lang,
                "source": "gemini_teacher",
            }

            # Cache the response for future zero-cost retrieval
            quota_guard.cache_response(f"code_teacher::{query}", result_payload)
            print(f"    [+] Successfully received Python code & explanation from Gemini Teacher.")
            return result_payload

        except Exception as exc:
            print(f"[!] Error calling Gemini Code Teacher: {exc}")
            return None


gemini_teacher = GeminiCodeTeacher()
