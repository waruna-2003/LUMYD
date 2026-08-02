from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.models.column import ColumnMetadata


class EvidenceService:
    @staticmethod
    def _load_data(file_path: str) -> pd.DataFrame:
        extension = Path(file_path).suffix.lower()
        return pd.read_csv(file_path) if extension == ".csv" else pd.read_excel(file_path)

    @staticmethod
    def build_combination_store(
        db: Session, dataset_id: str, file_path: str
    ) -> dict[str, dict[str, list[dict[str, object]]]]:
        data = EvidenceService._load_data(file_path)
        columns = (
            db.query(ColumnMetadata)
            .filter(ColumnMetadata.dataset_id == dataset_id)
            .all()
        )
        dimensions = [
            column.name
            for column in columns
            if column.business_role in {"DIMENSION", "ENTITY"}
            and not column.is_redundant
        ]
        measures = [
            column.name for column in columns if column.business_role == "MEASURE"
        ]

        store: dict[str, dict[str, list[dict[str, object]]]] = {}
        for dimension in dimensions:
            store[dimension] = {}
            for measure in measures:
                values = pd.to_numeric(data[measure], errors="coerce")
                grouped = (
                    pd.DataFrame({dimension: data[dimension], measure: values})
                    .dropna(subset=[dimension, measure])
                    .groupby(dimension)[measure]
                    .agg(["sum", "mean", "count"])
                    .reset_index()
                )
                store[dimension][measure] = [
                    {
                        "value": str(row[dimension]),
                        "sum": float(row["sum"]),
                        "mean": float(row["mean"]),
                        "count": int(row["count"]),
                    }
                    for _, row in grouped.iterrows()
                ]
        return store

    @staticmethod
    def get_ranked_evidence(
        db: Session,
        dataset_id: str,
        file_path: str,
        metric: str,
        dimension: str,
        limit: int = 20,
    ) -> dict[str, object]:
        columns = (
            db.query(ColumnMetadata)
            .filter(ColumnMetadata.dataset_id == dataset_id)
            .all()
        )
        by_name = {column.name: column for column in columns}
        metric_column = by_name.get(metric)
        dimension_column = by_name.get(dimension)

        if not metric_column or metric_column.business_role != "MEASURE":
            raise ValueError("Metric must be a column with the MEASURE role.")
        if not dimension_column or dimension_column.business_role not in {
            "DIMENSION",
            "ENTITY",
        }:
            raise ValueError("Dimension must have the DIMENSION or ENTITY role.")

        data = EvidenceService._load_data(file_path)
        numeric_metric = pd.to_numeric(data[metric], errors="coerce")
        analysis = pd.DataFrame(
            {"dimension": data[dimension], "metric": numeric_metric}
        ).dropna()
        if analysis.empty:
            return {
                "dataset_id": dataset_id,
                "metric": metric,
                "dimension": dimension,
                "global_mean": None,
                "evidence": [],
            }

        global_mean = float(analysis["metric"].mean())
        grouped = analysis.groupby("dimension")["metric"].agg(["sum", "mean", "count"])
        grouped["impact"] = (grouped["mean"] - global_mean) * grouped["count"]
        grouped["absolute_impact"] = grouped["impact"].abs()
        grouped = grouped.sort_values("absolute_impact", ascending=False).head(limit)

        return {
            "dataset_id": dataset_id,
            "metric": metric,
            "dimension": dimension,
            "global_mean": global_mean,
            "evidence": [
                {
                    "value": str(index),
                    "sum": float(row["sum"]),
                    "mean": float(row["mean"]),
                    "count": int(row["count"]),
                    "impact": float(row["impact"]),
                }
                for index, row in grouped.iterrows()
            ],
        }
