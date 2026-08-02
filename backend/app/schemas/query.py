from typing import Any

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


class QueryResponse(BaseModel):
    query_id: int
    structured_query: QueryStructure
    evidence_package: dict[str, Any]
