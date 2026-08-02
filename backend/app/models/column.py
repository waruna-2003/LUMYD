from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.session import Base


class ColumnMetadata(Base):
    __tablename__ = "column_metadata"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(
        String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String, nullable=False)
    data_type = Column(String, nullable=False)
    python_type = Column(String)
    is_nullable = Column(Boolean, default=True)

    dataset = relationship("Dataset", back_populates="column_metadata")
    stats = relationship(
        "ColumnStats",
        back_populates="column_metadata",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
