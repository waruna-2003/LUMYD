from pydantic import BaseModel

from app.schemas.column_stats import ColumnStatsResponse


class ColumnMetadataResponse(BaseModel):
    id: int
    dataset_id: str
    name: str
    data_type: str
    python_type: str | None
    is_nullable: bool
    technical_type: str | None = None
    business_type: str | None = None
    business_role: str | None = None
    unit: str | None = None
    aggregation: list[str] | None = None
    is_derived: bool = False
    is_redundant: bool = False
    stats: ColumnStatsResponse | None = None

    class Config:
        from_attributes = True
