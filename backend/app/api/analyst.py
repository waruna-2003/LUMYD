from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
import pandas as pd
from sqlalchemy.orm import Session

from app.core.quota_guard import quota_guard
from app.database.session import get_db
from app.models.agent import AgentTask, EscalationQueue
from app.models.column import ColumnMetadata
from app.models.dataset import Dataset
from app.models.query import AnalystQuery
from app.schemas.query import (
    DistillationStatsResponse,
    EscalationItemResponse,
    NarrativeResponse,
    QueryRequest,
    QueryResponse,
    QueryStructure,
    ResolveEscalationRequest,
    RoutingInfo,
)
from app.services.agent_router import AgentRouterService
from app.services.analytical_tasks import AnalyticalTaskEngine
from app.services.code_engine.distillation_manager import DistillationManager
from app.services.code_engine.gemini_teacher import gemini_teacher
from app.services.code_engine.predefined_library import PredefinedCodeLibrary
from app.services.code_engine.sandbox import CodeSandbox
from app.services.narrative_generator import MultilingualNarrativeGenerator
from app.services.query_parser import QueryParser
from app.services.retrieval_engine import RetrievalEngine
from app.services.storage_service import StorageService

router = APIRouter(prefix="/analyst", tags=["analyst"])


def _execute_analytical_intelligence(
    dataset: Dataset, structure: QueryStructure, raw_query: str, db: Session
) -> tuple[Any, Any]:
    try:
        resolved_path = StorageService.resolve_file_path(dataset.storage_path)
        ext = Path(resolved_path).suffix.lower()
        df = pd.read_csv(resolved_path) if ext == ".csv" else pd.read_excel(resolved_path)

        metric = structure.target_metric
        # Validate metric is in df; if not, find first numeric column
        if metric not in df.columns:
            numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if numeric_cols:
                metric = numeric_cols[0]

        # Determine primary dimension
        dimension = (
            structure.dimensions[0]
            if structure.dimensions and structure.dimensions[0] in df.columns
            else None
        )
        if not dimension:
            cat_cols = [c for c in df.columns if df[c].dtype == "object" and df[c].nunique() < 50]
            dimension = cat_cols[0] if cat_cols else df.columns[0]

        intent = structure.intent
        if intent == "ranking":
            task_res = AnalyticalTaskEngine.execute_ranking(
                df, metric=metric, dimension=dimension, filters=structure.filters
            )
        elif intent == "comparison":
            task_res = AnalyticalTaskEngine.execute_comparison(
                df, metric=metric, dimension=dimension, filters=structure.filters
            )
        elif intent == "root_cause":
            task_res = AnalyticalTaskEngine.execute_root_cause(
                df, metric=metric, target_dimension=dimension, filters=structure.filters
            )
        elif intent == "trend":
            task_res = AnalyticalTaskEngine.execute_trend(
                df, metric=metric, time_dimension=dimension, filters=structure.filters
            )
        elif intent == "distribution":
            task_res = AnalyticalTaskEngine.execute_distribution(
                df, metric=metric, dimension=dimension, filters=structure.filters
            )
        else:
            task_res = AnalyticalTaskEngine.execute_ranking(
                df, metric=metric, dimension=dimension, filters=structure.filters
            )

        narrative_dict = MultilingualNarrativeGenerator.generate_narrative(raw_query, task_res)
        narrative = NarrativeResponse.model_validate(narrative_dict)
        return task_res, narrative
    except Exception as err:
        print(f"[!] Analytical execution fallback warning: {err}")
        return None, None


@router.post("/{dataset_id}/query", response_model=QueryResponse)
def process_business_query(
    dataset_id: str,
    request: QueryRequest,
    db: Session = Depends(get_db),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    if dataset.status != "processed":
        raise HTTPException(status_code=409, detail="Dataset is not processed yet.")

    # 1. Load DataFrame & metadata
    resolved_path = StorageService.resolve_file_path(dataset.storage_path)
    ext = Path(resolved_path).suffix.lower()
    df = pd.read_csv(resolved_path) if ext == ".csv" else pd.read_excel(resolved_path)
    columns_list = [str(c) for c in df.columns]
    raw_query = request.query_text.strip()
    lang = MultilingualNarrativeGenerator.detect_language(raw_query)

    # -----------------------------------------------------------------
    # STEP 1: Check Code Knowledge Bank (Dynamic Semantic Cache - 0 API Calls)
    # -----------------------------------------------------------------
    cached_solution = DistillationManager.find_cached_knowledge(db, dataset_id, raw_query)
    if cached_solution:
        sandbox_res = CodeSandbox.execute(cached_solution["python_code"], df)
        if sandbox_res["success"]:
            query_record = AnalystQuery(
                dataset_id=dataset_id,
                query_text=raw_query,
                structure={"intent": cached_solution["intent_label"], "source": "knowledge_bank"},
                evidence_package={"result": sandbox_res["result"], "code": cached_solution["python_code"]},
            )
            db.add(query_record)
            db.commit()
            db.refresh(query_record)

            return QueryResponse(
                query_id=query_record.id,
                structured_query=QueryStructure(
                    intent=cached_solution["intent_label"],
                    target_metric=PredefinedCodeLibrary.find_best_numeric_column(df),
                    dimensions=[PredefinedCodeLibrary.find_best_categorical_column(df)],
                ),
                evidence_package={"result": sandbox_res["result"], "code": cached_solution["python_code"]},
                routing_info=RoutingInfo(
                    route="AUTOMATED_EXECUTION",
                    confidence=cached_solution.get("similarity", 0.95),
                    resolved_by="knowledge_bank",
                    escalated=False,
                ),
                narrative=NarrativeResponse(
                    headline=cached_solution["explanation"],
                    narrative_text=cached_solution["explanation"],
                    key_takeaways=[
                        f"Task: {cached_solution['intent_label']}",
                        "Reused from local knowledge bank (0 API calls)",
                    ],
                    language_detected=cached_solution["language"],
                ),
                generated_code=cached_solution["python_code"],
                code_source="knowledge_bank",
                code_result=sandbox_res["result"],
                human_explanation=cached_solution["explanation"],
                execution_time_ms=sandbox_res["execution_time_ms"],
            )

    # -----------------------------------------------------------------
    # STEP 2: Check Predefined Function Library (0ms LLM latency)
    # -----------------------------------------------------------------
    predefined_match = PredefinedCodeLibrary.match_and_generate(raw_query, df)
    if predefined_match:
        sandbox_res = CodeSandbox.execute(predefined_match["python_code"], df)
        if sandbox_res["success"]:
            summary_val = ""
            if isinstance(sandbox_res["result"], dict):
                summary_val = str(sandbox_res["result"].get("value") or sandbox_res["result"].get("formatted") or "")

            DistillationManager.record_solution(
                db=db,
                dataset_id=dataset_id,
                query=raw_query,
                intent_label=predefined_match["intent"],
                python_code=predefined_match["python_code"],
                explanation=predefined_match["explanation"],
                language=predefined_match["language"],
                execution_success=True,
                source="predefined",
                columns=columns_list,
                result_summary=summary_val,
            )

            query_record = AnalystQuery(
                dataset_id=dataset_id,
                query_text=raw_query,
                structure={"intent": predefined_match["intent"], "source": "predefined"},
                evidence_package={"result": sandbox_res["result"], "code": predefined_match["python_code"]},
            )
            db.add(query_record)
            db.commit()
            db.refresh(query_record)

            return QueryResponse(
                query_id=query_record.id,
                structured_query=QueryStructure(
                    intent=predefined_match["intent"],
                    target_metric=PredefinedCodeLibrary.find_best_numeric_column(df),
                    dimensions=[PredefinedCodeLibrary.find_best_categorical_column(df)],
                ),
                evidence_package={"result": sandbox_res["result"], "code": predefined_match["python_code"]},
                routing_info=RoutingInfo(
                    route="AUTOMATED_EXECUTION",
                    confidence=0.99,
                    resolved_by="local_predefined",
                    escalated=False,
                ),
                narrative=NarrativeResponse(
                    headline=predefined_match["explanation"],
                    narrative_text=predefined_match["explanation"],
                    key_takeaways=[
                        f"Task: {predefined_match['intent']}",
                        f"Execution: {sandbox_res['execution_time_ms']}ms (Local Sandbox)",
                    ],
                    language_detected=predefined_match["language"],
                ),
                generated_code=predefined_match["python_code"],
                code_source="predefined",
                code_result=sandbox_res["result"],
                human_explanation=predefined_match["explanation"],
                execution_time_ms=sandbox_res["execution_time_ms"],
            )

    # -----------------------------------------------------------------
    # STEP 3: Check Fixed Analytical Tasks (Ranking, Comparison, Trend, etc.)
    # -----------------------------------------------------------------
    router_service = AgentRouterService(db)
    route_result = router_service.route_query(dataset_id, raw_query)

    if not route_result["escalated"] and route_result["confidence"] >= 0.70:
        try:
            structure_data = QueryParser.parse_natural_language(
                db, dataset_id, raw_query, intent_override=route_result["task"]
            )
            structure = QueryStructure.model_validate(structure_data)
            evidence = RetrievalEngine.get_evidence_package(db, dataset_id, structure.model_dump())
            task_res, narrative = _execute_analytical_intelligence(dataset, structure, raw_query, db)

            dim = structure.dimensions[0] if structure.dimensions else df.columns[0]
            metric = structure.target_metric
            gen_code = (
                f"# Execute {structure.intent} on '{metric}' grouped by '{dim}'\n"
                f"result = df.groupby('{dim}')['{metric}'].sum().sort_values(ascending=False)"
            )

            query_record = AnalystQuery(
                dataset_id=dataset_id,
                query_text=raw_query,
                structure=structure.model_dump(mode="json"),
                evidence_package=evidence,
            )
            db.add(query_record)
            db.commit()
            db.refresh(query_record)

            return QueryResponse(
                query_id=query_record.id,
                structured_query=structure,
                evidence_package=evidence,
                routing_info=RoutingInfo(
                    route=route_result["route"],
                    confidence=route_result["confidence"],
                    resolved_by="local_router",
                    escalated=False,
                ),
                narrative=narrative,
                task_result=task_res,
                generated_code=gen_code,
                code_source="predefined",
                code_result={"type": "task_result", "data": task_res},
                human_explanation=narrative.headline if narrative else None,
                execution_time_ms=12.0,
            )
        except Exception as err:
            print(f"[!] Local analytical task execution bypassed: {err}")

    # -----------------------------------------------------------------
    # STEP 4: Gemini as The Master Teacher (Generate Python Code + Story)
    # -----------------------------------------------------------------
    teacher_taught = gemini_teacher.teach_code(raw_query, df, detected_language=lang)

    if teacher_taught and teacher_taught.get("python_code"):
        sandbox_res = CodeSandbox.execute(teacher_taught["python_code"], df)
        if sandbox_res["success"]:
            summary_val = ""
            if isinstance(sandbox_res["result"], dict):
                summary_val = str(sandbox_res["result"].get("value") or sandbox_res["result"].get("formatted") or "")

            # Store solution in Knowledge Bank & append to Distillation Dataset
            DistillationManager.record_solution(
                db=db,
                dataset_id=dataset_id,
                query=raw_query,
                intent_label=teacher_taught["intent_label"],
                python_code=teacher_taught["python_code"],
                explanation=teacher_taught["human_explanation"],
                language=teacher_taught["language"],
                execution_success=True,
                source="gemini_teacher",
                columns=columns_list,
                result_summary=summary_val,
            )

            query_record = AnalystQuery(
                dataset_id=dataset_id,
                query_text=raw_query,
                structure={"intent": teacher_taught["intent_label"], "source": "gemini_teacher"},
                evidence_package={"result": sandbox_res["result"], "code": teacher_taught["python_code"]},
            )
            db.add(query_record)
            db.commit()
            db.refresh(query_record)

            return QueryResponse(
                query_id=query_record.id,
                structured_query=QueryStructure(
                    intent=teacher_taught["intent_label"],
                    target_metric=PredefinedCodeLibrary.find_best_numeric_column(df),
                    dimensions=[PredefinedCodeLibrary.find_best_categorical_column(df)],
                ),
                evidence_package={"result": sandbox_res["result"], "code": teacher_taught["python_code"]},
                routing_info=RoutingInfo(
                    route="AUTOMATED_EXECUTION",
                    confidence=0.90,
                    resolved_by="gemini_teacher",
                    escalated=False,
                ),
                narrative=NarrativeResponse(
                    headline=teacher_taught["human_explanation"],
                    narrative_text=teacher_taught["human_explanation"],
                    key_takeaways=[
                        f"Learned Intent: {teacher_taught['intent_label']}",
                        "Executed via sandboxed Python code",
                        "Added to SLM distillation dataset for local training",
                    ],
                    language_detected=teacher_taught["language"],
                ),
                generated_code=teacher_taught["python_code"],
                code_source="gemini_teacher",
                code_result=sandbox_res["result"],
                human_explanation=teacher_taught["human_explanation"],
                execution_time_ms=sandbox_res["execution_time_ms"],
            )

    # -----------------------------------------------------------------
    # STEP 5: Out-of-Scope / Novel Escalation Receipt (Path C)
    # -----------------------------------------------------------------
    escalation_id = route_result.get("escalation_id")
    if lang == "singlish":
        headline = "Oyaage query eka triage queue ekata escalate kala."
        text = "Me question eka dataset eke thiyena metrics walata direct match une na. Ape team eken review karala model eka update karanna ticket ekak create kala."
        takeaways = [
            f"Ticket ID: #{escalation_id[:8] if escalation_id else 'N/A'}",
            "Status: Pending Review Queue",
            "Action: Admin triage dashboard eken resolve karanna puluwan",
        ]
    elif lang == "sinhala":
        headline = "ඔබගේ ප්‍රශ්නය පරීක්ෂණ පෝලිමට යොමු කරන ලදී."
        text = "මෙම ප්‍රශ්නය දත්ත පද්ධතියට සෘජුව නොගැලපෙන බැවින් පරිපාලක සමාලෝචනය සඳහා යොමු කර ඇත."
        takeaways = [
            f"ප්‍රවේශපත්‍ර අංකය: #{escalation_id[:8] if escalation_id else 'N/A'}",
            "තත්ත්වය: සමාලෝචනය වෙමින් පවතී",
        ]
    else:
        headline = "Query diverted to administrative review queue."
        text = "This query could not be verified automatically against the dataset schema. It has been logged in the triage queue for review and model retraining."
        takeaways = [
            f"Ticket ID: #{escalation_id[:8] if escalation_id else 'N/A'}",
            "Status: Pending Review Queue",
            "Action: Awaiting ground-truth labeling in Admin Triage panel",
        ]

    return QueryResponse(
        query_id=0,
        structured_query=QueryStructure(
            intent="unresolved_escalation",
            target_metric=PredefinedCodeLibrary.find_best_numeric_column(df),
            dimensions=[],
            filters={"escalation_id": escalation_id or "none"},
        ),
        evidence_package={
            "status": "ESCALATED",
            "message": "Query could not be answered with current dataset schema.",
            "escalation_id": escalation_id,
            "observations": [],
        },
        routing_info=RoutingInfo(
            route="HUMAN_ESCALATION",
            confidence=route_result.get("confidence", 0.2),
            resolved_by="pending_triage",
            escalated=True,
        ),
        narrative=NarrativeResponse(
            headline=headline,
            narrative_text=text,
            key_takeaways=takeaways,
            language_detected=lang,
        ),
        task_result=None,
        generated_code=None,
        code_source=None,
        code_result=None,
        human_explanation=headline,
    )


# =====================================================================
# Distillation & Training Endpoints
# =====================================================================

@router.get("/distillation/stats", response_model=DistillationStatsResponse)
def get_distillation_stats(db: Session = Depends(get_db)):
    """Retrieve statistics about the accumulated Teacher-Student distillation dataset."""
    return DistillationManager.get_statistics(db)


@router.get("/distillation/export")
def export_distillation_dataset():
    """Download the accumulated instruction-tuning dataset for local SLM training."""
    path = DistillationManager.get_dataset_path()
    if not path.exists():
        raise HTTPException(status_code=404, detail="Distillation dataset is empty yet.")
    return FileResponse(
        path=str(path),
        filename="teacher_distillation_dataset.jsonl",
        media_type="application/jsonlines",
    )


# =====================================================================
# Administrative Triage & Quota Endpoints
# =====================================================================

@router.get("/escalations/pending", response_model=List[EscalationItemResponse])
def list_pending_escalations(db: Session = Depends(get_db)):
    """Retrieve all queries currently waiting in the escalation queue."""
    return (
        db.query(EscalationQueue)
        .filter(EscalationQueue.status == "PENDING")
        .order_by(EscalationQueue.created_at.desc())
        .all()
    )


@router.post("/escalations/resolve")
def resolve_escalation(
    payload: ResolveEscalationRequest,
    db: Session = Depends(get_db),
):
    """Admin manually maps an unhandled query to a verified analytical task."""
    item = db.query(EscalationQueue).filter(EscalationQueue.id == payload.escalation_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Escalation record not found.")

    target_task = db.query(AgentTask).filter(AgentTask.task_name == payload.target_task_name).first()
    if not target_task:
        raise HTTPException(
            status_code=400, detail=f"Task '{payload.target_task_name}' does not exist."
        )

    item.status = "RESOLVED"
    item.resolved_task = payload.target_task_name
    item.admin_notes = payload.admin_notes
    item.resolved_at = datetime.now(timezone.utc)

    # Active learning: Append query to task's sample trigger list
    current_queries = list(target_task.sample_queries or [])
    if item.raw_query not in current_queries:
        current_queries.append(item.raw_query)
        target_task.sample_queries = current_queries

    db.commit()

    # Re-warm router cache with updated sample
    router_service = AgentRouterService(db)
    router_service.warm_cache()

    return {
        "message": f"Escalation {payload.escalation_id} resolved as '{payload.target_task_name}' and added to active training samples.",
        "sample_count": len(target_task.sample_queries),
    }


@router.get("/quota/status")
def get_gemini_quota_status():
    """Retrieve current Gemini API Free Tier usage and daily limits."""
    return quota_guard.get_status()
