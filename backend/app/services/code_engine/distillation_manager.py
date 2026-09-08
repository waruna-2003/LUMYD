"""LUMYD Distillation Manager & Code Knowledge Bank

Manages the accumulation of verified (query, schema, python_code, result,
explanation)
tuples taught by Gemini or predefined functions. Serves as a dynamic semantic
cache
for local code reuse and exports instruction-tuning datasets for fine-tuning
local SLMs.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.code_knowledge import CodeKnowledgeBank

DISTILLATION_FILE = Path("backend/data/teacher_distillation_dataset.jsonl")


class DistillationManager:
    """Orchestrates code reuse from the Knowledge Bank and manages the training

    dataset distillation for local SLMs.
    """

    @classmethod
    def get_dataset_path(cls) -> Path:
        # Support running from root or backend
        if Path("backend/data").exists():
            return Path("backend/data/teacher_distillation_dataset.jsonl")
        elif Path("data").exists():
            return Path("data/teacher_distillation_dataset.jsonl")
        else:
            p = Path("backend/data/teacher_distillation_dataset.jsonl")
            p.parent.mkdir(parents=True, exist_ok=True)
            return p

    @classmethod
    def find_cached_knowledge(
        cls,
        db: Session,
        dataset_id: str,
        query: str,
        similarity_threshold: float = 0.88,
    ) -> Optional[Dict[str, Any]]:
        """Searches the CodeKnowledgeBank for an exact or high-confidence semantic match."""
        # 1. Exact query match first
        exact = (
            db.query(CodeKnowledgeBank)
            .filter(
                CodeKnowledgeBank.dataset_id == dataset_id,
                CodeKnowledgeBank.query_text.ilike(query.strip()),
                CodeKnowledgeBank.execution_success.is_(True),
            )
            .first()
        )
        if exact:
            exact.execution_count += 1
            exact.last_executed_at = datetime.now(timezone.utc)
            db.commit()
            return {
                "intent_label": exact.intent_label,
                "python_code": exact.python_code,
                "explanation": exact.explanation,
                "language": exact.language,
                "source": "knowledge_bank",
                "similarity": 1.0,
            }

        # 2. Semantic lookup if entries exist
        records = (
            db.query(CodeKnowledgeBank)
            .filter(
                CodeKnowledgeBank.dataset_id == dataset_id,
                CodeKnowledgeBank.execution_success.is_(True),
            )
            .all()
        )
        if not records:
            return None

        # Lightweight keyword / word overlap check before neural embedding
        q_tokens = set(query.lower().split())
        best_record = None
        best_score = 0.0

        for r in records:
            r_tokens = set(r.query_text.lower().split())
            if not r_tokens:
                continue
            jaccard = len(q_tokens & r_tokens) / len(q_tokens | r_tokens)
            if jaccard > best_score:
                best_score = jaccard
                best_record = r

        if best_record and best_score >= similarity_threshold:
            best_record.execution_count += 1
            best_record.last_executed_at = datetime.now(timezone.utc)
            db.commit()
            return {
                "intent_label": best_record.intent_label,
                "python_code": best_record.python_code,
                "explanation": best_record.explanation,
                "language": best_record.language,
                "source": "knowledge_bank",
                "similarity": round(best_score, 3),
            }

        return None

    @classmethod
    def record_solution(
        cls,
        db: Session,
        dataset_id: str,
        query: str,
        intent_label: str,
        python_code: str,
        explanation: str,
        language: str,
        execution_success: bool,
        source: str,
        columns: List[str],
        result_summary: Optional[str] = None,
    ) -> CodeKnowledgeBank:
        """Stores a verified code solution in PostgreSQL and appends it to the

        SLM distillation dataset.
        """
        # 1. Save or update PostgreSQL record
        existing = (
            db.query(CodeKnowledgeBank)
            .filter(
                CodeKnowledgeBank.dataset_id == dataset_id,
                CodeKnowledgeBank.query_text == query.strip(),
            )
            .first()
        )
        if existing:
            existing.python_code = python_code
            existing.explanation = explanation
            existing.language = language
            existing.execution_success = execution_success
            existing.execution_count += 1
            existing.last_executed_at = datetime.now(timezone.utc)
            db_record = existing
        else:
            db_record = CodeKnowledgeBank(
                dataset_id=dataset_id,
                query_text=query.strip(),
                intent_label=intent_label,
                python_code=python_code,
                explanation=explanation,
                language=language,
                execution_success=execution_success,
                execution_count=1,
                source=source,
            )
            db.add(db_record)
        db.commit()
        db.refresh(db_record)

        # 2. Append to Distillation JSONL if execution was successful
        if execution_success:
            distill_path = cls.get_dataset_path()
            distill_path.parent.mkdir(parents=True, exist_ok=True)

            instruction_record = {
                "instruction": (
                    "You are a helpful business intelligence code generator and data analyst. "
                    "Given the dataframe schema and the user question, write Python code operating on `df` "
                    "to compute the exact answer in variable `result`, and explain the findings in a friendly, "
                    "human-readable manner in the user's dialect."
                ),
                "dataset_id": dataset_id,
                "dataset_columns": columns,
                "query": query.strip(),
                "language": language,
                "intent_label": intent_label,
                "python_code": python_code.strip(),
                "human_explanation": explanation.strip(),
                "result_summary": str(result_summary) if result_summary is not None else "",
                "source": source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            try:
                with open(distill_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(instruction_record, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f"[!] Warning: Failed to append to distillation dataset: {e}")

        return db_record

    @classmethod
    def get_statistics(cls, db: Session) -> Dict[str, Any]:
        """Calculates current distillation metrics for the Teacher-Student

        flywheel.
        """
        total_in_db = db.query(CodeKnowledgeBank).count()
        successful_in_db = (
            db.query(CodeKnowledgeBank)
            .filter(CodeKnowledgeBank.execution_success.is_(True))
            .count()
        )
        gemini_taught = (
            db.query(CodeKnowledgeBank)
            .filter(CodeKnowledgeBank.source == "gemini_teacher")
            .count()
        )
        predefined_count = (
            db.query(CodeKnowledgeBank)
            .filter(CodeKnowledgeBank.source == "predefined")
            .count()
        )

        distill_path = cls.get_dataset_path()
        file_lines = 0
        file_size_bytes = 0
        if distill_path.exists():
            file_size_bytes = distill_path.stat().st_size
            with open(distill_path, "r", encoding="utf-8") as f:
                file_lines = sum(1 for _ in f)

        return {
            "total_knowledge_records": total_in_db,
            "verified_executable_solutions": successful_in_db,
            "learned_from_gemini_teacher": gemini_taught,
            "predefined_solutions": predefined_count,
            "distillation_dataset_lines": file_lines,
            "distillation_file_bytes": file_size_bytes,
            "distillation_file_path": str(distill_path),
            "ready_for_slm_fine_tuning": file_lines >= 50,
        }
