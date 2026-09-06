#!/usr/bin/env python3
"""
LUMYD Synthetic Query Generator
Generates diverse business intelligence queries across multiple intents
(root_cause, ranking, comparison, trend, distribution) in English and Singlish,
pairing each query with its ground-truth structured intent and slot parameters.
"""

import argparse
import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from backend/.env or root .env
BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")
load_dotenv(ROOT_DIR / ".env")

from app.core.quota_guard import quota_guard

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class IntentSlotStructure(BaseModel):
    intent: str
    target_metric: str
    dimensions: List[str] = Field(default_factory=list)
    filters: Dict[str, Any] = Field(default_factory=dict)
    time_period: Optional[str] = None
    granularity: str = "month"


class SyntheticQueryRecord(BaseModel):
    query: str
    language: str
    intent_json: IntentSlotStructure


TASK_DEFINITIONS = [
    {
        "intent": "root_cause",
        "description": "User wants to investigate why a business metric dropped, rose, or deviated from expectations.",
        "metrics": ["sales", "profit", "revenue", "cost", "conversion_rate", "churn_rate"],
        "dimensions": ["region", "product_category", "sales_rep", "channel", "branch"],
        "singlish_seed_phrases": [
            "sales adu une ai mcn",
            "revenue bahinna pradhana hethuwa mokakda",
            "profit drop una reason eka hoyala denna",
            "last month sales me tharam adu ai kiyala kiyanna",
            "kandy branch eke profit adu une mokada",
            "ai me quarter eke cost eka ochchara wadi",
            "salli adu una hethuwa explain karanna puluwanda"
        ]
    },
    {
        "intent": "ranking",
        "description": "User wants to find top or bottom performing entities, products, branches, or segments.",
        "metrics": ["revenue", "sales_volume", "profit", "order_count", "discount"],
        "dimensions": ["sales_rep", "product_name", "region", "customer_segment", "branch"],
        "singlish_seed_phrases": [
            "wadiyenma revenue thiyenne kaatada",
            "top 5 rep la kauda me maase wadiyenma salli genapu",
            "aduwema wikunapu products monawada",
            "lowest sales thiyena branches list eka denna",
            "highest profit dunna category monada",
            "best performing region eka mokakda",
            "top 10 customers la pennanna"
        ]
    },
    {
        "intent": "comparison",
        "description": "User wants to compare performance across multiple groups, regions, categories, or channels.",
        "metrics": ["sales", "profit_margin", "revenue", "average_order_value"],
        "dimensions": ["region", "channel", "product_type", "department"],
        "singlish_seed_phrases": [
            "colombo branch ekai kandy branch ekai compare karanna",
            "western province saha central province athara revenue wenasa mokakda",
            "retail and wholesale profit eka compare karala balanna",
            "online sales vs retail store sales performance kohomada",
            "me deka athara wenasa pennanna puluwanda"
        ]
    },
    {
        "intent": "trend",
        "description": "User wants to track how a business metric changes over days, weeks, months, or quarters.",
        "metrics": ["monthly_sales", "quarterly_revenue", "daily_orders", "profit_growth"],
        "dimensions": ["order_date", "month", "quarter", "year"],
        "singlish_seed_phrases": [
            "last 6 months wala sales trend eka kohomada",
            "revenue eka masen maseta wadi wenawada adu wenawada",
            "quarterly profit movement eka analyze karanna",
            "daily order volume eke wenasweema pennanna",
            "year over year growth eka kohomada balanna"
        ]
    },
    {
        "intent": "distribution",
        "description": "User wants to see the spread, range, or concentration of transactions, order values, or discounts.",
        "metrics": ["order_amount", "discount_percentage", "unit_price", "deal_size"],
        "dimensions": ["price_bracket", "discount_range", "frequency"],
        "singlish_seed_phrases": [
            "order amounts wala distribution eka kohomada spread wela thiyenne",
            "discount percentage eka spread wela thiyena widiha pennanna",
            "deal sizes wala frequency eka balanna puluwanda",
            "godak orders fall wenne mona price range ekatada",
            "order value histogram eka kohomada"
        ]
    }
]


def generate_offline_mock_data(samples_per_intent: int) -> List[Dict[str, Any]]:
    """Generates realistic synthetic data offline without API calls for testing & bootstrapping."""
    records: List[Dict[str, Any]] = []

    casual_templates = [
        ("why did {metric} drop so hard in {dimension}?", "root_cause", "casual_en"),
        ("what made {metric} go down last month?", "root_cause", "casual_en"),
        ("who brought in the most {metric} this quarter?", "ranking", "casual_en"),
        ("show me bottom 5 {dimension} by {metric}", "ranking", "casual_en"),
        ("how does {dimension} A compare with B on {metric}?", "comparison", "casual_en"),
        ("is {metric} going up or down over time?", "trend", "casual_en"),
        ("how are {metric} numbers distributed across {dimension}?", "distribution", "casual_en"),
    ]

    formal_templates = [
        ("Identify the primary operational drivers behind the decline in {metric} for {dimension}.", "root_cause", "en"),
        ("What are the top-ranking {dimension} entities evaluated by aggregate {metric}?", "ranking", "en"),
        ("Provide a comparative performance analysis of {metric} segmented by {dimension}.", "comparison", "en"),
        ("Evaluate the month-over-month trajectory and momentum of {metric}.", "trend", "en"),
        ("Analyze the dispersion and statistical distribution of {metric} across tiers.", "distribution", "en"),
    ]

    for task in TASK_DEFINITIONS:
        intent = task["intent"]
        metrics = task["metrics"]
        dims = task["dimensions"]
        singlish_seeds = task["singlish_seed_phrases"]

        count_generated = 0
        while count_generated < samples_per_intent:
            metric = random.choice(metrics)
            dim = random.choice(dims)
            lang_choice = random.choices(["singlish", "en", "casual_en"], weights=[0.4, 0.35, 0.25])[0]

            if lang_choice == "singlish":
                base_seed = random.choice(singlish_seeds)
                # Apply minor variations to seed
                variations = [
                    base_seed,
                    f"{base_seed} mcn",
                    f"mata {base_seed} puluwanda",
                    f"ane {base_seed}",
                    f"{dim} eke {base_seed}"
                ]
                query_text = random.choice(variations)
            elif lang_choice == "en":
                template = random.choice([t[0] for t in formal_templates if t[1] == intent])
                query_text = template.format(metric=metric, dimension=dim)
            else:
                template = random.choice([t[0] for t in casual_templates if t[1] == intent])
                query_text = template.format(metric=metric, dimension=dim)

            record = {
                "query": query_text,
                "language": lang_choice,
                "intent_json": {
                    "intent": intent,
                    "target_metric": metric,
                    "dimensions": [dim],
                    "filters": {},
                    "time_period": random.choice(["last_month", "q3", "last_year", None]),
                    "granularity": random.choice(["day", "month", "quarter"])
                }
            }
            records.append(record)
            count_generated += 1

    return records


def generate_with_gemini(api_key: str, samples_per_intent: int) -> List[Dict[str, Any]]:
    """Calls the Google Gemini API to generate high-diversity multi-dialect query records."""
    if not GENAI_AVAILABLE:
        raise RuntimeError("google-genai SDK is not installed.")

    client = genai.Client(api_key=api_key)
    model_name = "gemini-3.6-flash"
    all_records: List[Dict[str, Any]] = []

    for task in TASK_DEFINITIONS:
        intent = task["intent"]
        description = task["description"]
        seed_samples = task["singlish_seed_phrases"]
        metrics = ", ".join(task["metrics"])
        dims = ", ".join(task["dimensions"])

        prompt = f"""
You are an advanced synthetic training data generator for LUMYD, an analytical business intelligence engine.
Your task is to generate {samples_per_intent} diverse natural language queries that users would ask for the intent: "{intent}".
Intent Description: {description}

Candidate metrics: {metrics}
Candidate dimensions: {dims}

Crucial Language & Dialect Distribution Requirements:
1. Exactly ~35% Formal Enterprise Business English (clean, professional, precise)
2. Exactly ~25% Casual/Colloquial English (spoken style, slang, lowercase, typos, contractions)
3. Exactly ~40% Authentic Singlish (Sinhala phonetic words transliterated into English alphabet, code-mixed with English business terms).
   Authentic Singlish phrasing examples for inspiration:
   {json.dumps(seed_samples, indent=2)}

Output Requirements:
Return ONLY a valid JSON array of objects conforming exactly to this structure:
[
  {{
    "query": "the user query text (English or Singlish)",
    "language": "en | casual_en | singlish",
    "intent_json": {{
      "intent": "{intent}",
      "target_metric": "selected metric from candidates",
      "dimensions": ["selected dimension from candidates"],
      "filters": {{}},
      "time_period": "string description of period or null",
      "granularity": "day | week | month | quarter | year"
    }}
  }}
]
"""

        # Quota check before each batch
        can_req, reason = quota_guard.can_request()
        if not can_req:
            print(f"    [!] Gemini Quota limit reached: {reason}")
            print("    [*] Falling back to seeded samples for this intent to protect API limits.")
            fallback_batch = [
                r for r in generate_offline_mock_data(samples_per_intent)
                if r["intent_json"]["intent"] == intent
            ]
            all_records.extend(fallback_batch)
            continue

        print(f"[*] Calling Gemini ({model_name}) for intent: '{intent}' ({samples_per_intent} samples)...")
        
        # Enforce rate limit (guarantees < 15 RPM)
        quota_guard.throttle_and_record()

        max_retries = 3
        success = False
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.75,
                    )
                )

                batch = json.loads(response.text)
                if isinstance(batch, list):
                    # Validate against schema
                    validated_batch = []
                    for item in batch:
                        try:
                            record = SyntheticQueryRecord.model_validate(item)
                            validated_batch.append(record.model_dump())
                        except Exception as val_err:
                            print(f"    [!] Skipping item failing validation: {val_err}")
                    all_records.extend(validated_batch)
                    print(f"    [+] Successfully collected {len(validated_batch)} validated samples.")
                    success = True
                    break
                else:
                    print(f"    [!] Unexpected non-list response for intent: {intent}")
                    break
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "resource_exhausted" in err_str:
                    wait_time = (2 ** attempt) * 10
                    print(f"    [!] Rate limited (429). Backing off for {wait_time} seconds (attempt {attempt + 1}/{max_retries})...")
                    import time
                    time.sleep(wait_time)
                else:
                    print(f"    [!] Error generating batch for intent '{intent}': {e}")
                    break

        if not success:
            print("    [*] Falling back to seeded samples for this intent.")
            fallback_batch = [
                r for r in generate_offline_mock_data(samples_per_intent)
                if r["intent_json"]["intent"] == intent
            ]
            all_records.extend(fallback_batch)

    return all_records


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic query dataset for LUMYD Active Learning.")
    parser.add_argument(
        "--samples-per-intent",
        type=int,
        default=40,
        help="Number of queries to generate per intent (default: 40, total 200 across 5 intents)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(BACKEND_DIR / "data" / "synthetic_training_data.json"),
        help="Path to output JSON file"
    )
    parser.add_argument(
        "--offline-mock",
        action="store_true",
        help="Generate synthetic dataset offline using deterministic seed templates without calling Gemini API"
    )
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.offline_mock or not api_key:
        if not api_key and not args.offline_mock:
            print("[!] GEMINI_API_KEY environment variable not found in environment or backend/.env.")
            print("[*] Proceeding with offline seed generation (--offline-mock mode).")
        else:
            print("[*] Running in --offline-mock mode...")
        records = generate_offline_mock_data(args.samples_per_intent)
    else:
        print("[*] GEMINI_API_KEY detected. Initiating Gemini synthetic data generation...")
        records = generate_with_gemini(api_key, args.samples_per_intent)

    # Save output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    if sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("\n" + "=" * 60)
    print(f"[OK] Successfully generated {len(records)} synthetic query records.")
    print(f"[OK] Saved to: {output_path}")

    # Summary statistics
    intents = {}
    languages = {}
    for r in records:
        intent = r["intent_json"]["intent"]
        lang = r.get("language", "unknown")
        intents[intent] = intents.get(intent, 0) + 1
        languages[lang] = languages.get(lang, 0) + 1

    print("\nBreakdown by Intent:")
    for intent, count in intents.items():
        print(f"  - {intent}: {count}")

    print("\nBreakdown by Language:")
    for lang, count in languages.items():
        print(f"  - {lang}: {count} ({count/len(records)*100:.1f}%)")

    # Quota report
    status = quota_guard.get_status()
    print("\nGemini Free Tier Quota Status:")
    print(f"  - Requests used today: {status['requests_used_today']} / {status['daily_safety_limit']} ({status['percentage_used']}%)")
    print(f"  - Requests remaining today: {status['requests_remaining']}")
    print(f"  - Total requests all-time: {status['total_all_time']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
