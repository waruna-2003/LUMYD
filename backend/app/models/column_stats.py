from sqlalchemy import JSON, Column, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database.session import Base


class ColumnStats(Base):
    __tablename__ = "column_stats"

    id = Column(Integer, primary_key=True, index=True)
    column_id = Column(
        Integer,
        ForeignKey("column_metadata.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    mean = Column(Float, nullable=True)
    median = Column(Float, nullable=True)
    min_val = Column(Float, nullable=True)
    max_val = Column(Float, nullable=True)
    std_dev = Column(Float, nullable=True)
    unique_count = Column(Integer, nullable=False, default=0)
    null_count = Column(Integer, nullable=False, default=0)
    outlier_count = Column(Integer, nullable=False, default=0)
    distribution = Column(JSON, nullable=True)

    column_metadata = relationship("ColumnMetadata", back_populates="stats")
