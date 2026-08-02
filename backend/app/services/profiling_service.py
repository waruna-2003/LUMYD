import math
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.column import ColumnMetadata
from app.models.column_stats import ColumnStats


class ProfilingService:
    @staticmethod
    def profile_columns(db: Session, dataset_id: str, file_path: str) -> None:
        extension = Path(file_path).suffix.lower()
        data = pd.read_csv(file_path) if extension == ".csv" else pd.read_excel(file_path)
        columns = (
            db.query(ColumnMetadata)
            .filter(ColumnMetadata.dataset_id == dataset_id)
            .all()
        )

        for column in columns:
            series = data[column.name]
            stats_data = {
                "unique_count": int(series.nunique(dropna=True)),
                "null_count": int(series.isnull().sum()),
                "outlier_count": 0,
                "distribution": None,
            }

            if column.data_type == "numeric":
                numeric_series = pd.to_numeric(series, errors="coerce").dropna()
                if not numeric_series.empty:
                    standard_deviation = float(numeric_series.std())
                    stats_data.update(
                        {
                            "mean": float(numeric_series.mean()),
                            "median": float(numeric_series.median()),
                            "min_val": float(numeric_series.min()),
                            "max_val": float(numeric_series.max()),
                            "std_dev": (
                                standard_deviation
                                if math.isfinite(standard_deviation)
                                else None
                            ),
                        }
                    )

                    first_quartile = numeric_series.quantile(0.25)
                    third_quartile = numeric_series.quantile(0.75)
                    interquartile_range = third_quartile - first_quartile
                    outliers = numeric_series[
                        (numeric_series < first_quartile - 1.5 * interquartile_range)
                        | (numeric_series > third_quartile + 1.5 * interquartile_range)
                    ]
                    stats_data["outlier_count"] = int(len(outliers))

                    counts, bins = np.histogram(numeric_series, bins=10)
                    stats_data["distribution"] = {
                        "labels": [
                            f"{bins[index]:.1f}-{bins[index + 1]:.1f}"
                            for index in range(len(bins) - 1)
                        ],
                        "values": counts.astype(int).tolist(),
                    }
            elif column.data_type == "categorical":
                top_values = series.value_counts().head(10)
                stats_data["distribution"] = {
                    "labels": top_values.index.astype(str).tolist(),
                    "values": top_values.values.astype(int).tolist(),
                }

            if column.stats:
                for field, value in stats_data.items():
                    setattr(column.stats, field, value)
            else:
                db.add(ColumnStats(column_id=column.id, **stats_data))

        db.commit()
