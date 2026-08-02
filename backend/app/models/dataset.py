import uuid

from sqlalchemy import BigInteger, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database.session import Base

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    storage_path = Column("filepath", String, nullable=False)
    filetype = Column(String, nullable=False)
    filesize = Column(BigInteger, nullable=False)
    row_count = Column("rows", Integer, nullable=False, default=0)
    column_count = Column("columns", Integer, nullable=False, default=0)
    status = Column(String, default="uploaded")
    created_at = Column("uploaded_at", DateTime(timezone=True), server_default=func.now())
