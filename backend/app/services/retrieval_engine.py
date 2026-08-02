from typing import Any

from sqlalchemy.orm import Session

from app.models.knowledge import FactCombination, PairwiseEvidence


class RetrievalEngine:
    @staticmethod
    def get_evidence_package(
        db: Session, dataset_id: str, structure: dict[str, Any]
    ) -> dict[str, Any]:
        metric = str(structure["target_metric"])
        requested_dimensions = set(structure.get("dimensions", []))
        filters = structure.get("filters", {})

        relationships = (
            db.query(PairwiseEvidence)
            .filter(
                PairwiseEvidence.dataset_id == dataset_id,
                PairwiseEvidence.column_b == metric,
                PairwiseEvidence.rel_type == "cat_num",
            )
            .order_by(PairwiseEvidence.strength_score.desc())
            .all()
        )
        if requested_dimensions:
            relationships = [
                row for row in relationships if row.column_a in requested_dimensions
            ]
        relationships = relationships[:3]

        facts = (
            db.query(FactCombination)
            .filter(FactCombination.dataset_id == dataset_id)
            .all()
        )
        sum_key = f"{metric}_sum"
        mean_key = f"{metric}_mean"
        count_key = f"{metric}_count"
        observations: list[dict[str, Any]] = []

        for relationship in relationships:
            dimension = relationship.column_a
            breakdown = [
                fact
                for fact in facts
                if dimension in fact.dimensions and sum_key in fact.metrics
            ]
            if dimension in filters:
                breakdown = [
                    fact
                    for fact in breakdown
                    if str(fact.dimensions[dimension]).lower()
                    == str(filters[dimension]).lower()
                ]

            total = sum(abs(float(fact.metrics[sum_key])) for fact in breakdown)
            for fact in breakdown:
                metric_value = float(fact.metrics[sum_key])
                strength = float(relationship.strength_score or 0)
                contribution = abs(metric_value) / total if total else 0.0
                observations.append(
                    {
                        "fact_id": fact.id,
                        "relationship_id": relationship.id,
                        "factor": f"{dimension}: {fact.dimensions[dimension]}",
                        "dimension": dimension,
                        "dimension_value": fact.dimensions[dimension],
                        "metric": metric,
                        "metric_value": metric_value,
                        "metric_mean": fact.metrics.get(mean_key),
                        "row_count": fact.metrics.get(count_key),
                        "relationship_strength": strength,
                        "contribution_score": contribution,
                        "relevance_score": strength * contribution,
                        "type": "statistical_evidence",
                    }
                )

        observations.sort(
            key=lambda item: item["relevance_score"], reverse=True
        )
        return {
            "main_metric": metric,
            "intent": structure["intent"],
            "filters_applied": filters,
            "influencers_considered": [row.column_a for row in relationships],
            "observations": observations[:10],
        }
