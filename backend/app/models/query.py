from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database.session import Base


class AnalystQuery(Base):
    __tablename__ = "analyst_queries"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(
        String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query_text = Column(Text, nullable=False)
    structure = Column(JSON, nullable=False)
    evidence_package = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
