from datetime import datetime, timezone
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.quota_guard import quota_guard
from app.database.session import get_db
from app.models.agent import AgentTask, EscalationQueue
from app.models.column import ColumnMetadata
from app.models.dataset import Dataset
from app.models.query import AnalystQuery
from app.schemas.query import (
    EscalationItemResponse,
    QueryRequest,
    QueryResponse,
    QueryStructure,
    ResolveEscalationRequest,
    RoutingInfo,
)
from app.services.agent_router import AgentRouterService
from app.services.gemini_triage_service import gemini_triage
from app.services.query_parser import QueryParser
from app.services.retrieval_engine import RetrievalEngine

router = APIRouter(prefix="/analyst", tags=["analyst"])


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

    # 1. Evaluate with local Semantic Router
    router_service = AgentRouterService(db)
    route_result = router_service.route_query(dataset_id, request.query_text)

    # -------------------------------------------------------------
    # PATH A: High-Confidence In-Distribution Match (Local Zero-Cost Execution)
    # -------------------------------------------------------------
    if not route_result["escalated"]:
        try:
            structure_data = QueryParser.parse_natural_language(
                db, dataset_id, request.query_text, intent_override=route_result["task"]
            )
            structure = QueryStructure.model_validate(structure_data)
            evidence = RetrievalEngine.get_evidence_package(
                db, dataset_id, structure.model_dump()
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        query = AnalystQuery(
            dataset_id=dataset_id,
            query_text=request.query_text,
            structure=structure.model_dump(mode="json"),
            evidence_package=evidence,
        )
        db.add(query)
        db.commit()
        db.refresh(query)

        return QueryResponse(
            query_id=query.id,
            structured_query=structure,
            evidence_package=evidence,
            routing_info=RoutingInfo(
                route=route_result["route"],
                confidence=route_result["confidence"],
                resolved_by="local_router",
                escalated=False,
            ),
        )

    # -------------------------------------------------------------
    # PATH B: Low-Confidence / Novel Intent -> Automated Gemini Fallback
    # -------------------------------------------------------------
    escalation_id = route_result.get("escalation_id")
    columns = db.query(ColumnMetadata).filter(ColumnMetadata.dataset_id == dataset_id).all()
    available_metrics = [
        col.name for col in columns if col.business_role in {"MEASURE", "RATE"}
    ]
    available_dimensions = [
        col.name
        for col in columns
        if col.business_role in {"DIMENSION", "ENTITY", "TIME_DIMENSION"}
        and not col.is_redundant
    ]

    triage_result = gemini_triage.resolve_ambiguous_query(
        request.query_text, available_metrics, available_dimensions
    )

    if triage_result:
        # 1. Update escalation queue record to RESOLVED
        if escalation_id:
            escalation_item = db.query(EscalationQueue).filter(EscalationQueue.id == escalation_id).first()
            if escalation_item:
                escalation_item.status = "RESOLVED"
                escalation_item.resolved_task = triage_result["intent"]
                escalation_item.admin_notes = "Auto-resolved via Gemini Triage"
                escalation_item.resolved_at = datetime.now(timezone.utc)

        # 2. Active Learning: Append query to AgentTask.sample_queries for future local matches
        target_task = (
            db.query(AgentTask).filter(AgentTask.task_name == triage_result["intent"]).first()
        )
        if target_task:
            current_samples = list(target_task.sample_queries or [])
            if request.query_text not in current_samples:
                current_samples.append(request.query_text)
                target_task.sample_queries = current_samples
                db.commit()
                # Refresh local centroid cache so future identical/similar queries hit locally
                router_service.warm_cache()

        structure = QueryStructure.model_validate(triage_result)
        evidence = RetrievalEngine.get_evidence_package(
            db, dataset_id, structure.model_dump()
        )

        query = AnalystQuery(
            dataset_id=dataset_id,
            query_text=request.query_text,
            structure=structure.model_dump(mode="json"),
            evidence_package=evidence,
        )
        db.add(query)
        db.commit()
        db.refresh(query)

        return QueryResponse(
            query_id=query.id,
            structured_query=structure,
            evidence_package=evidence,
            routing_info=RoutingInfo(
                route="AUTOMATED_EXECUTION",
                confidence=route_result["confidence"],
                resolved_by="gemini_triage",
                escalated=False,
            ),
        )

    # -------------------------------------------------------------
    # PATH C: Unresolvable / Out-of-Domain -> Safely Return Escalation Receipt
    # -------------------------------------------------------------
    return QueryResponse(
        query_id=0,
        structured_query=QueryStructure(
            intent="unresolved_escalation",
            target_metric=available_metrics[0] if available_metrics else "unknown",
            dimensions=[],
            filters={"escalation_id": escalation_id or "none"},
        ),
        evidence_package={
            "status": "ESCALATED",
            "message": route_result.get(
                "message",
                "Query could not be verified automatically. Logged to triage queue for review.",
            ),
            "escalation_id": escalation_id,
            "observations": [],
        },
        routing_info=RoutingInfo(
            route="HUMAN_ESCALATION",
            confidence=route_result["confidence"],
            resolved_by="pending_triage",
            escalated=True,
        ),
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
