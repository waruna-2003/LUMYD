import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database.session import Base


class CodeKnowledgeBank(Base):
    """Stores verified code solutions, human narratives, and execution metadata

    taught by Gemini (The Teacher) or predefined functions. Serves as a dynamic
    knowledge bank for local reuse and SLM training dataset distillation.
    """

    __tablename__ = "code_knowledge_bank"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(
        String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query_text = Column(String(1000), nullable=False, index=True)
    intent_label = Column(String(100), nullable=False, index=True)
    python_code = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    language = Column(String(20), default="english", nullable=False)
    execution_success = Column(Boolean, default=True, nullable=False)
    execution_count = Column(Integer, default=1, nullable=False)
    source = Column(String(50), default="gemini_teacher", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_executed_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
