import os
from fastapi import HTTPException, UploadFile

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def validate_dataset_file(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required.")
    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV and Excel allowed.")
    if file.size is not None and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size must not exceed 50MB.")
    return True
