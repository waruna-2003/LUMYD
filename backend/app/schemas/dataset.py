from pydantic import BaseModel
from datetime import datetime
class DatasetBase(BaseModel):
    filename: str

class DatasetCreate(DatasetBase):
    storage_path: str

class DatasetResponse(DatasetBase):
    id: str
    status: str
    row_count: int
    column_count: int
    created_at: datetime

    class Config:
        from_attributes = True
