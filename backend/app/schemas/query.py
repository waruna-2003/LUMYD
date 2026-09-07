from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query_text: str = Field(min_length=3, max_length=2000)


class QueryStructure(BaseModel):
    intent: str
    target_metric: str
    dimensions: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    time_period: str | None = None
    comparison_period: str | None = None
    granularity: str = "month"


class RoutingInfo(BaseModel):
    route: str
    confidence: float
    resolved_by: str  # "local_router", "gemini_triage", "pending_triage"
    escalated: bool


class QueryResponse(BaseModel):
    query_id: int
    structured_query: QueryStructure
    evidence_package: dict[str, Any]
    routing_info: Optional[RoutingInfo] = None


class ResolveEscalationRequest(BaseModel):
    escalation_id: str
    target_task_name: str
    admin_notes: Optional[str] = None


class EscalationItemResponse(BaseModel):
    id: str
    dataset_id: str
    raw_query: str
    confidence_score: float
    predicted_task: Optional[str] = None
    status: str
    resolved_task: Optional[str] = None
    admin_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
