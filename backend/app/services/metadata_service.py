from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.column import ColumnMetadata
from app.models.dataset import Dataset
from app.services.profiling_service import ProfilingService


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

        for column_name in data.columns:
            series = data[column_name]
            db.add(
                ColumnMetadata(
                    dataset_id=dataset.id,
                    name=str(column_name),
                    data_type=MetadataService._infer_business_type(series),
                    python_type=str(series.dtype),
                    is_nullable=bool(series.isnull().any()),
                )
            )

        db.commit()
        ProfilingService.profile_columns(db, dataset_id, dataset.storage_path)
        dataset.status = "processed"
        db.commit()

    @staticmethod
    def _infer_business_type(series: pd.Series) -> str:
        column_name = str(series.name).lower()
        if pd.api.types.is_datetime64_any_dtype(series) or "date" in column_name:
            return "datetime"
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"

        non_null = series.dropna()
        unique_count = non_null.nunique()
        unique_ratio = unique_count / len(non_null) if len(non_null) else 1
        if unique_ratio < 0.15 or unique_count < 30:
            return "categorical"
        return "text"
