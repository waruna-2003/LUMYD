import os
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.dataset import Dataset
from app.schemas.dataset import DatasetResponse
from app.services.storage_service import StorageService
from app.utils.validators import validate_dataset_file

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    validate_dataset_file(file)

    content = await file.read()
    file_path = StorageService.save_file(content, file.filename)

    try:
        extension = Path(file.filename).suffix.lower()
        if extension == ".csv":
            data = pd.read_csv(file_path)
        else:
            data = pd.read_excel(file_path)

        new_dataset = Dataset(
            name=Path(file.filename).stem,
            filename=file.filename,
            storage_path=file_path,
            filetype=extension,
            filesize=len(content),
            row_count=len(data.index),
            column_count=len(data.columns),
            status="uploaded",
        )
        db.add(new_dataset)
        db.commit()
        db.refresh(new_dataset)
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
