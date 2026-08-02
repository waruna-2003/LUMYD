from pydantic import BaseModel


class DistributionResponse(BaseModel):
    labels: list[str]
    values: list[int]


class ColumnStatsResponse(BaseModel):
    id: int
    column_id: int
    mean: float | None
    median: float | None
    min_val: float | None
    max_val: float | None
    std_dev: float | None
    unique_count: int
    null_count: int
    outlier_count: int
    distribution: DistributionResponse | None

    class Config:
        from_attributes = True
