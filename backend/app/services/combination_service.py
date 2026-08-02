import hashlib
import json

import pandas as pd
from sqlalchemy.orm import Session

from app.models.knowledge import FactCombination


class CombinationService:
    @staticmethod
    def build_store(
        db: Session,
        dataset_id: str,
        data: pd.DataFrame,
        dimensions: list[str],
        measures: list[str],
    ) -> None:
        db.query(FactCombination).filter(
            FactCombination.dataset_id == dataset_id
        ).delete(synchronize_session=False)

        if not dimensions or not measures:
            db.commit()
            return

        numeric_data = data.copy()
        valid_measures: list[str] = []
        for measure in measures:
            numeric_data[measure] = pd.to_numeric(numeric_data[measure], errors="coerce")
            if numeric_data[measure].notna().any():
                valid_measures.append(measure)

        for dimension in dimensions:
            if not valid_measures:
                break
            grouped = numeric_data.groupby(dimension, dropna=False)[valid_measures].agg(
                ["sum", "mean", "count"]
            )
            for value, row in grouped.iterrows():
                dimension_value = "(null)" if pd.isna(value) else str(value)
                dimensions_data = {dimension: dimension_value}
                metrics: dict[str, float | int] = {}
                for measure in valid_measures:
                    metrics[f"{measure}_sum"] = float(row[(measure, "sum")])
                    metrics[f"{measure}_mean"] = float(row[(measure, "mean")])
                    metrics[f"{measure}_count"] = int(row[(measure, "count")])

                hash_value = hashlib.sha256(
                    json.dumps(dimensions_data, sort_keys=True).encode("utf-8")
                ).hexdigest()
                db.add(
                    FactCombination(
                        dataset_id=dataset_id,
                        dimensions=dimensions_data,
                        metrics=metrics,
                        combination_hash=hash_value,
                    )
                )
        db.commit()
