#!/usr/bin/env python3
"""
LUMYD Agent Task Seeder
Seeds the 5 core analytical tasks into the PostgreSQL `agent_tasks` table,
populating sample trigger queries from synthetic training data and curated seed phrases.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database.session import SessionLocal
from app.models.agent import AgentTask

SYNTHETIC_DATA_FILE = BACKEND_DIR / "data" / "synthetic_training_data.json"

DEFAULT_TASKS = [
    {
        "task_name": "root_cause",
        "description": "Explains why a metric dropped, rose, or diverged from expected values.",
        "handler_service": "retrieval_engine",
        "curated_samples": [
            "why did sales drop last month",
            "what caused profit reduction",
            "sales adu une ai mcn",
            "profit bahinna hethuwa mokakda",
            "revenue drop una reason eka explain karanna",
            "why did revenue decline in q3",
            "salli adu una hethuwa explain karanna puluwanda",
            "investigate the sudden increase in operating costs"
        ]
    },
    {
        "task_name": "ranking",
        "description": "Finds highest or lowest performing entities, branches, products, or reps.",
        "handler_service": "retrieval_engine",
        "curated_samples": [
            "top selling items",
            "who generated the most profit",
            "wadiyenma revenue thiyenne kaatada",
            "lowest performing branches",
            "aduwema wikunapu products monawada",
            "show me the top 5 sales reps this quarter",
            "best performing region eka mokakda",
            "rank customers by total order volume"
        ]
    },
    {
        "task_name": "comparison",
        "description": "Compares performance across multiple segments, regions, categories, or channels.",
        "handler_service": "retrieval_engine",
        "curated_samples": [
            "compare sales between regions",
            "colombo branch ekai kandy branch ekai compare karanna",
            "western province saha central province compare karanna",
            "difference between retail and wholesale revenue",
            "compare profit margin online vs in-store",
            "how do channel A and channel B compare in sales"
        ]
    },
    {
        "task_name": "trend",
        "description": "Tracks trajectory and momentum of metrics over days, weeks, months, or quarters.",
        "handler_service": "retrieval_engine",
        "curated_samples": [
            "how have sales trended over the past 6 months",
            "monthly revenue growth trajectory",
            "revenue eka masen maseta wadi wenawada adu wenawada",
            "quarterly profit movement eka analyze karanna",
            "is daily order volume increasing or decreasing",
            "year over year growth trend for units sold"
        ]
    },
    {
        "task_name": "distribution",
        "description": "Analyzes the statistical distribution, spread, frequency, or histogram of a measure.",
        "handler_service": "retrieval_engine",
        "curated_samples": [
            "what is the distribution of order sizes",
            "how are discount percentages spread across transactions",
            "order amounts wala distribution eka kohomada",
            "histogram of deal values",
            "deal sizes wala frequency eka balanna puluwanda",
            "show price range distribution for orders"
        ]
    }
]


def load_synthetic_queries_by_intent() -> Dict[str, List[str]]:
    """Loads and groups queries from synthetic_training_data.json by intent."""
    intent_queries: Dict[str, List[str]] = {t["task_name"]: [] for t in DEFAULT_TASKS}
    if not SYNTHETIC_DATA_FILE.exists():
        print(f"[*] Synthetic data file not found at {SYNTHETIC_DATA_FILE}. Using curated seeds only.")
        return intent_queries

    try:
        with open(SYNTHETIC_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            intent = item.get("intent_json", {}).get("intent")
            query = item.get("query")
            if intent in intent_queries and query:
                intent_queries[intent].append(query.strip())
        print(f"[+] Loaded {len(data)} synthetic samples from {SYNTHETIC_DATA_FILE}")
    except Exception as e:
        print(f"[!] Warning: Failed to read synthetic data: {e}")

    return intent_queries


def seed_tasks() -> None:
    db = SessionLocal()
    try:
        synthetic_queries = load_synthetic_queries_by_intent()
        total_seeded = 0

        for task_def in DEFAULT_TASKS:
            task_name = task_def["task_name"]
            existing = db.query(AgentTask).filter(AgentTask.task_name == task_name).first()

            # Merge curated and synthetic queries without duplicates
            combined_queries = list(task_def["curated_samples"])
            for q in synthetic_queries.get(task_name, []):
                if q not in combined_queries:
                    combined_queries.append(q)

            if existing:
                # Merge into existing sample_queries
                existing_set = set(existing.sample_queries or [])
                for q in combined_queries:
                    existing_set.add(q)
                existing.sample_queries = list(existing_set)
                existing.description = task_def["description"]
                existing.handler_service = task_def["handler_service"]
                print(f"[+] Updated task '{task_name}' with {len(existing.sample_queries)} sample queries.")
                total_seeded += len(existing.sample_queries)
            else:
                new_task = AgentTask(
                    task_name=task_name,
                    description=task_def["description"],
                    handler_service=task_def["handler_service"],
                    sample_queries=combined_queries,
                    is_active=True
                )
                db.add(new_task)
                print(f"[+] Created task '{task_name}' with {len(combined_queries)} sample queries.")
                total_seeded += len(combined_queries)

        db.commit()
        print("\n" + "=" * 60)
        print(f"[OK] Agent tasks seeded successfully in PostgreSQL! ({total_seeded} total sample queries)")
        print("=" * 60)
    except Exception as e:
        db.rollback()
        print(f"[!] Error seeding agent tasks: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_tasks()
