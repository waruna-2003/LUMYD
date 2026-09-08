"""
Ingests the 4 sample domain datasets into the LUMYD PostgreSQL database:
- retail_sales.csv
- hr_workforce.csv
- finance_expenses.csv
- inventory_supply.csv

Runs MetadataService to extract semantics, column stats, relationships, and combinations.
"""

import sys
import os
from pathlib import Path

# Add backend directory to sys.path so app imports work
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.models.dataset import Dataset
from app.services.storage_service import StorageService
from app.services.metadata_service import MetadataService

SAMPLE_FILES = [
    "retail_sales.csv",
    "hr_workforce.csv",
    "finance_expenses.csv",
    "inventory_supply.csv",
]

def ingest_domains():
    sample_dir = backend_dir / "data" / "sample_domains"
    if not sample_dir.exists():
        print(f"Error: Sample domain directory does not exist at {sample_dir}")
        return

    db = SessionLocal()
    try:
        for filename in SAMPLE_FILES:
            file_path = sample_dir / filename
            if not file_path.exists():
                print(f"Skipping {filename}: file not found.")
                continue

            # Check if dataset already exists in database
            existing = db.query(Dataset).filter(Dataset.filename == filename).first()
            if existing:
                print(f"Removing existing record for {filename} (ID: {existing.id})...")
                db.delete(existing)
                db.commit()

            print(f"Ingesting {filename}...")
            with open(file_path, "rb") as f:
                content = f.read()

            storage_path = StorageService.save_file(content, filename)
            dataset = Dataset(
                name=Path(filename).stem.replace("_", " ").title(),
                filename=filename,
                storage_path=storage_path,
                filetype=".csv",
                filesize=len(content),
                row_count=0,
                column_count=0,
                status="processing",
            )
            db.add(dataset)
            db.commit()
            db.refresh(dataset)

            print(f"  Created Dataset ID: {dataset.id}")
            print("  Extracting metadata & semantic profiling...")
            MetadataService.extract_metadata(dataset.id)

            # Refresh to see updated info
            db.refresh(dataset)
            print(f"  Status: {dataset.status}, Rows: {dataset.row_count}, Columns: {dataset.column_count}")
            print(f"  Successfully ingested {filename}!\n")

    except Exception as e:
        print(f"Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    ingest_domains()
