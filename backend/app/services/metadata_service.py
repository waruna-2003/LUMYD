from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.column import ColumnMetadata
from app.models.dataset import Dataset
from app.services.profiling_service import ProfilingService
from app.services.semantic_service import SemanticService
from app.services.relationship_engine import RelationshipEngine
from app.services.combination_service import CombinationService


class MetadataService:
    @staticmethod
    def extract_metadata(dataset_id: str) -> None:
        db = SessionLocal()
        try:
            MetadataService._process_dataset(db, dataset_id)
        except Exception:
            db.rollback()
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if dataset:
                dataset.status = "error"
                db.commit()
            raise
        finally:
            db.close()

    @staticmethod
    def _process_dataset(db: Session, dataset_id: str) -> None:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            return

        extension = Path(dataset.storage_path).suffix.lower()
        if extension == ".csv":
            data = pd.read_csv(dataset.storage_path)
        else:
            data = pd.read_excel(dataset.storage_path)

        dataset.row_count = len(data.index)
        dataset.column_count = len(data.columns)
        dataset.status = "processing"

        db.query(ColumnMetadata).filter(
            ColumnMetadata.dataset_id == dataset.id
        ).delete(synchronize_session=False)

        derived_columns = SemanticService.detect_derived_redundancy(data)

        for column_name in data.columns:
            series = data[column_name]
            semantic = SemanticService.infer_semantic_metadata(str(column_name), series)
            semantic["is_derived"] = str(column_name) in derived_columns
            semantic["is_redundant"] = str(column_name) in derived_columns
            db.add(
                ColumnMetadata(
                    dataset_id=dataset.id,
                    name=str(column_name),
                    data_type=str(semantic["business_type"]).lower(),
                    python_type=str(series.dtype),
                    is_nullable=bool(series.isnull().any()),
                    **semantic,
                )
            )

        db.commit()
        ProfilingService.profile_columns(db, dataset_id, dataset.storage_path)

        columns = (
            db.query(ColumnMetadata)
            .filter(ColumnMetadata.dataset_id == dataset_id)
            .all()
        )
        dimensions = [
            column.name
            for column in columns
            if column.business_role in {"DIMENSION", "ENTITY"}
            and not column.is_redundant
        ]
        measures = [
            column.name for column in columns if column.business_role == "MEASURE"
        ]

        RelationshipEngine.compute_all_evidence(db, dataset_id, data)
        CombinationService.build_store(db, dataset_id, data, dimensions, measures)

        dataset.status = "processed"
        db.commit()
