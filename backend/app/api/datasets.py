import os
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.column import ColumnMetadata
from app.models.dataset import Dataset
from app.schemas.column import ColumnMetadataResponse
from app.schemas.dataset import DatasetResponse
from app.services.metadata_service import MetadataService
from app.services.storage_service import StorageService
from app.utils.validators import validate_dataset_file

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    validate_dataset_file(file)

    content = await file.read()
    file_path = StorageService.save_file(content, file.filename)

    try:
        extension = Path(file.filename).suffix.lower()

        new_dataset = Dataset(
            name=Path(file.filename).stem,
            filename=file.filename,
            storage_path=file_path,
            filetype=extension,
            filesize=len(content),
            row_count=0,
            column_count=0,
            status="processing",
        )
        db.add(new_dataset)
        db.commit()
        db.refresh(new_dataset)
        background_tasks.add_task(MetadataService.extract_metadata, new_dataset.id)
        return new_dataset
    except Exception as error:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500, detail=f"File processing error: {error}"
        ) from error


@router.get("", response_model=list[DatasetResponse])
def list_datasets(db: Session = Depends(get_db)):
    return db.query(Dataset).all()


@router.get("/{dataset_id}/schema", response_model=list[ColumnMetadataResponse])
def get_dataset_schema(dataset_id: str, db: Session = Depends(get_db)):
    dataset = db.query(Dataset.id).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return (
        db.query(ColumnMetadata)
        .filter(ColumnMetadata.dataset_id == dataset_id)
        .order_by(ColumnMetadata.id)
        .all()
    )
