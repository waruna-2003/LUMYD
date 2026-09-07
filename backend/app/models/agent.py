import uuid
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.sql import func

from app.database.session import Base


class AgentTask(Base):
    """Stores all verified analytical tasks and sample intent phrases."""

    __tablename__ = "agent_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    handler_service = Column(String(100), nullable=False, default="retrieval_engine")
    sample_queries = Column(JSON, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EscalationQueue(Base):
    """Captures unhandled, ambiguous, or novel intent queries for human or automated LLM triage."""

    __tablename__ = "escalation_queue"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(
        String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_query = Column(String(1000), nullable=False)
    confidence_score = Column(Float, nullable=False)
    predicted_task = Column(String(100), nullable=True)
    status = Column(String(50), default="PENDING", nullable=False, index=True)
    resolved_task = Column(String(100), nullable=True)
    admin_notes = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
