from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.dataset import Dataset
from app.models.query import AnalystQuery
from app.schemas.query import QueryRequest, QueryResponse, QueryStructure
from app.services.query_parser import QueryParser
from app.services.retrieval_engine import RetrievalEngine

router = APIRouter(prefix="/analyst", tags=["analyst"])


@router.post("/{dataset_id}/query", response_model=QueryResponse)
def process_business_query(
    dataset_id: str,
    request: QueryRequest,
    db: Session = Depends(get_db),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    if dataset.status != "processed":
        raise HTTPException(status_code=409, detail="Dataset is not processed yet.")

    try:
        structure_data = QueryParser.parse_natural_language(
            db, dataset_id, request.query_text
        )
        structure = QueryStructure.model_validate(structure_data)
        evidence = RetrievalEngine.get_evidence_package(
            db, dataset_id, structure.model_dump()
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    query = AnalystQuery(
        dataset_id=dataset_id,
        query_text=request.query_text,
        structure=structure.model_dump(mode="json"),
        evidence_package=evidence,
    )
    db.add(query)
    db.commit()
    db.refresh(query)

    return QueryResponse(
        query_id=query.id,
        structured_query=structure,
        evidence_package=evidence,
    )
