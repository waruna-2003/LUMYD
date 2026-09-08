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


class NarrativeResponse(BaseModel):
    headline: str
    narrative_text: str
    key_takeaways: list[str] = Field(default_factory=list)
    language_detected: str  # "english", "singlish", "sinhala"


class QueryResponse(BaseModel):
    query_id: int
    structured_query: QueryStructure
    evidence_package: dict[str, Any]
    routing_info: Optional[RoutingInfo] = None
    narrative: Optional[NarrativeResponse] = None
    task_result: Optional[dict[str, Any]] = None
    # Code-Gen & Teacher-Student Distillation fields
    generated_code: Optional[str] = None
    code_source: Optional[str] = None  # "predefined", "knowledge_bank", "gemini_teacher"
    code_result: Optional[dict[str, Any]] = None
    human_explanation: Optional[str] = None
    execution_time_ms: Optional[float] = None


class DistillationStatsResponse(BaseModel):
    total_knowledge_records: int
    verified_executable_solutions: int
    learned_from_gemini_teacher: int
    predefined_solutions: int
    distillation_dataset_lines: int
    distillation_file_bytes: int
    distillation_file_path: str
    ready_for_slm_fine_tuning: bool


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
