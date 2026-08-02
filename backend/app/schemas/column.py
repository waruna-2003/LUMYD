from pydantic import BaseModel

from app.schemas.column_stats import ColumnStatsResponse


class ColumnMetadataResponse(BaseModel):
    id: int
    dataset_id: str
    name: str
    data_type: str
    python_type: str | None
    is_nullable: bool
    stats: ColumnStatsResponse | None = None

    class Config:
        from_attributes = True
