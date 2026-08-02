import re

from sqlalchemy.orm import Session

from app.models.column import ColumnMetadata
from app.models.knowledge import FactCombination


class QueryParser:
    @staticmethod
    def _matches(text: str, value: str) -> bool:
        normalized_value = re.sub(r"[_\-]+", " ", value.lower()).strip()
        variants = {normalized_value}
        if not normalized_value.endswith("s"):
            variants.add(f"{normalized_value}s")
        if normalized_value.endswith("y"):
            variants.add(f"{normalized_value[:-1]}ies")
        return any(
            re.search(rf"(?<!\w){re.escape(variant)}(?!\w)", text)
            for variant in variants
        )

    @staticmethod
    def parse_natural_language(
        db: Session, dataset_id: str, query_text: str
    ) -> dict[str, object]:
        text = re.sub(r"[_\-]+", " ", query_text.lower())
        columns = (
            db.query(ColumnMetadata)
            .filter(ColumnMetadata.dataset_id == dataset_id)
            .all()
        )
        metrics = [
            column.name
            for column in columns
            if column.business_role in {"MEASURE", "RATE"}
        ]
        dimensions = [
            column.name
            for column in columns
            if column.business_role in {
                "DIMENSION",
                "ENTITY",
                "TIME_DIMENSION",
            }
            and not column.is_redundant
        ]
        if not metrics:
            raise ValueError("This dataset has no recognized business metrics.")

        matched_metrics = [
            metric for metric in metrics if QueryParser._matches(text, metric)
        ]
        target_metric = matched_metrics[0] if matched_metrics else metrics[0]
        matched_dimensions = [
            dimension
            for dimension in dimensions
            if QueryParser._matches(text, dimension)
        ]

        intent = "trend"
        if any(word in text for word in ("why", "cause", "reason", "driver")):
            intent = "root_cause"
        elif any(word in text for word in ("compare", "versus", " vs ")):
            intent = "comparison"
        elif any(word in text for word in ("top", "best", "rank", "highest", "lowest")):
            intent = "ranking"
        elif any(word in text for word in ("distribution", "spread", "frequency")):
            intent = "distribution"

        filters: dict[str, str] = {}
        facts = (
            db.query(FactCombination)
            .filter(FactCombination.dataset_id == dataset_id)
            .all()
        )
        for fact in facts:
            for dimension, value in fact.dimensions.items():
                value_text = str(value)
                if QueryParser._matches(text, value_text):
                    filters[dimension] = value_text

        time_period = None
        comparison_period = None
        if "quarter" in text:
            time_period = "last_quarter"
        elif "year" in text:
            time_period = "last_year"
        elif "month" in text:
            time_period = "last_month"
        if any(word in text for word in ("previous", "prior", "last year")):
            comparison_period = "previous_period"

        granularity = "month"
        for candidate in ("day", "week", "quarter", "year"):
            if candidate in text:
                granularity = candidate
                break

        return {
            "intent": intent,
            "target_metric": target_metric,
            "dimensions": matched_dimensions,
            "filters": filters,
            "time_period": time_period,
            "comparison_period": comparison_period,
            "granularity": granularity,
        }
