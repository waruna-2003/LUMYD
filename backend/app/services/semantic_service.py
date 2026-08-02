import pandas as pd


class SemanticService:
    @staticmethod
    def infer_semantic_metadata(
        column_name: str, series: pd.Series
    ) -> dict[str, object]:
        name = column_name.lower()
        unique_count = int(series.nunique(dropna=True))
        non_null_count = int(series.notna().sum())
        cardinality_ratio = unique_count / non_null_count if non_null_count else 1

        metadata: dict[str, object] = {
            "technical_type": str(series.dtype),
            "business_type": "TEXT",
            "business_role": "DIMENSION",
            "unit": None,
            "aggregation": ["count"],
            "is_derived": False,
            "is_redundant": False,
        }

        identifier_tokens = ("id", "key", "code", "number")
        name_tokens = name.replace("-", "_").split("_")
        if any(token in identifier_tokens for token in name_tokens) or (
            cardinality_ratio == 1 and unique_count > 0
        ):
            metadata["business_role"] = "IDENTIFIER"
            return metadata

        if (
            pd.api.types.is_datetime64_any_dtype(series)
            or "date" in name
            or "time" in name
        ):
            metadata["business_type"] = "DATETIME"
            metadata["business_role"] = "TIME_DIMENSION"
            return metadata

        if pd.api.types.is_numeric_dtype(series):
            metadata["business_type"] = "NUMERIC"
            if any(
                keyword in name
                for keyword in ("price", "amount", "sales", "revenue", "cost")
            ):
                metadata.update(
                    business_role="MEASURE",
                    unit="currency",
                    aggregation=["sum", "mean", "median"],
                )
            elif any(
                keyword in name for keyword in ("discount", "rate", "percent")
            ) or (not series.dropna().empty and series.dropna().max() <= 1):
                metadata.update(
                    business_role="RATE",
                    unit="percentage",
                    aggregation=["mean"],
                )
            else:
                metadata.update(
                    business_role="MEASURE", aggregation=["sum", "mean"]
                )
            return metadata

        if unique_count < 50 or cardinality_ratio < 0.2:
            metadata["business_type"] = "CATEGORICAL"
            if any(keyword in name for keyword in ("rep", "employee", "customer")):
                metadata["business_role"] = "ENTITY"
        return metadata

    @staticmethod
    def detect_derived_redundancy(data: pd.DataFrame) -> set[str]:
        """Find text columns that contain two other text columns in sampled rows."""
        derived: set[str] = set()
        text_columns = list(data.select_dtypes(include=["object", "string"]).columns)

        for target in text_columns:
            candidates = [column for column in text_columns if column != target]
            for first_index, first in enumerate(candidates):
                for second in candidates[first_index + 1 :]:
                    sample = data[[target, first, second]].dropna().head(20)
                    if sample.empty:
                        continue
                    is_concatenation = sample.apply(
                        lambda row: str(row[first]) in str(row[target])
                        and str(row[second]) in str(row[target]),
                        axis=1,
                    ).all()
                    if is_concatenation:
                        derived.add(str(target))
                        break
                if target in derived:
                    break
        return derived
