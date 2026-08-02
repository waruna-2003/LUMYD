from sqlalchemy import JSON, Column, Float, ForeignKey, Index, Integer, String, UniqueConstraint

from app.database.session import Base


class FactCombination(Base):
    """Compact aggregated facts grouped by business dimensions."""

    __tablename__ = "fact_combinations"
    __table_args__ = (
        UniqueConstraint(
            "dataset_id", "combination_hash", name="uq_fact_dataset_combination"
        ),
        Index("idx_fact_dataset", "dataset_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(
        String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    dimensions = Column(JSON, nullable=False)
    metrics = Column(JSON, nullable=False)
    combination_hash = Column(String, nullable=False, index=True)


class PairwiseEvidence(Base):
    """Persisted statistical evidence between semantic columns."""

    __tablename__ = "pairwise_evidence"
    __table_args__ = (
        UniqueConstraint(
            "dataset_id",
            "column_a",
            "column_b",
            "rel_type",
            name="uq_pairwise_relationship",
        ),
        Index("idx_pairwise_dataset", "dataset_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(
        String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    column_a = Column(String, nullable=False)
    column_b = Column(String, nullable=False)
    rel_type = Column(String, nullable=False)
    strength_score = Column(Float, nullable=True)
    significance_score = Column(Float, nullable=True)
    evidence_data = Column(JSON, nullable=True)
