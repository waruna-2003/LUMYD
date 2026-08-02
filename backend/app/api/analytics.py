from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.dataset import Dataset
from app.models.knowledge import FactCombination, PairwiseEvidence
from app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/{dataset_id}/evidence")
def get_ranked_evidence(
    dataset_id: str,
    metric: str,
    dimension: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    if dataset.status != "processed":
        raise HTTPException(status_code=409, detail="Dataset is not processed yet.")

    facts = (
        db.query(FactCombination)
        .filter(FactCombination.dataset_id == dataset_id)
        .all()
    )
    matching_facts = [fact for fact in facts if dimension in fact.dimensions]
    mean_key = f"{metric}_mean"
    count_key = f"{metric}_count"
    sum_key = f"{metric}_sum"
    matching_facts = [
        fact
        for fact in matching_facts
        if mean_key in fact.metrics and count_key in fact.metrics
    ]
    if matching_facts:
        total_count = sum(int(fact.metrics[count_key]) for fact in matching_facts)
        total_sum = sum(float(fact.metrics[sum_key]) for fact in matching_facts)
        global_mean = total_sum / total_count if total_count else 0.0
        ranked = []
        for fact in matching_facts:
            mean = float(fact.metrics[mean_key])
            count = int(fact.metrics[count_key])
            ranked.append(
                {
                    "value": fact.dimensions[dimension],
                    "sum": float(fact.metrics[sum_key]),
                    "mean": mean,
                    "count": count,
                    "impact": (mean - global_mean) * count,
                }
            )
        ranked.sort(key=lambda item: abs(item["impact"]), reverse=True)
        return {
            "dataset_id": dataset_id,
            "metric": metric,
            "dimension": dimension,
            "global_mean": global_mean,
            "source": "combination_store",
            "evidence": ranked[:limit],
        }

    try:
        result = EvidenceService.get_ranked_evidence(
            db,
            dataset_id,
            dataset.storage_path,
            metric,
            dimension,
            limit,
        )
        result["source"] = "raw_dataset"
        return result
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{dataset_id}/relationships")
def list_relationship_evidence(
    dataset_id: str,
    minimum_strength: float = Query(default=0.0, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
):
    if not db.query(Dataset.id).filter(Dataset.id == dataset_id).first():
        raise HTTPException(status_code=404, detail="Dataset not found.")
    rows = (
        db.query(PairwiseEvidence)
        .filter(
            PairwiseEvidence.dataset_id == dataset_id,
            PairwiseEvidence.strength_score >= minimum_strength,
        )
        .order_by(PairwiseEvidence.strength_score.desc())
        .all()
    )
    return [
        {
            "id": row.id,
            "column_a": row.column_a,
            "column_b": row.column_b,
            "relationship_type": row.rel_type,
            "strength_score": row.strength_score,
            "significance_score": row.significance_score,
            "evidence": row.evidence_data,
        }
        for row in rows
    ]


@router.get("/{dataset_id}/facts")
def list_fact_combinations(
    dataset_id: str,
    dimension: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    if not db.query(Dataset.id).filter(Dataset.id == dataset_id).first():
        raise HTTPException(status_code=404, detail="Dataset not found.")
    rows = (
        db.query(FactCombination)
        .filter(FactCombination.dataset_id == dataset_id)
        .order_by(FactCombination.id)
        .all()
    )
    if dimension:
        rows = [row for row in rows if dimension in row.dimensions]
    return [
        {
            "id": row.id,
            "dimensions": row.dimensions,
            "metrics": row.metrics,
            "combination_hash": row.combination_hash,
        }
        for row in rows[:limit]
    ]
