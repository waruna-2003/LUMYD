import math

import pandas as pd
from scipy.stats import f_oneway, pearsonr
from sqlalchemy.orm import Session

from app.models.column import ColumnMetadata
from app.models.knowledge import PairwiseEvidence


class RelationshipEngine:
    @staticmethod
    def compute_all_evidence(
        db: Session, dataset_id: str, data: pd.DataFrame
    ) -> None:
        columns = (
            db.query(ColumnMetadata)
            .filter(ColumnMetadata.dataset_id == dataset_id)
            .all()
        )
        measures = [
            column
            for column in columns
            if column.business_role in {"MEASURE", "RATE"}
        ]
        dimensions = [
            column
            for column in columns
            if column.business_role in {"DIMENSION", "ENTITY"}
            and not column.is_redundant
        ]

        db.query(PairwiseEvidence).filter(
            PairwiseEvidence.dataset_id == dataset_id
        ).delete(synchronize_session=False)

        evidence: list[PairwiseEvidence] = []
        for dimension in dimensions:
            for measure in measures:
                frame = pd.DataFrame(
                    {
                        "dimension": data[dimension.name],
                        "measure": pd.to_numeric(data[measure.name], errors="coerce"),
                    }
                ).dropna()
                if frame.empty:
                    continue

                grouped = frame.groupby("dimension")["measure"].agg(
                    ["mean", "count", "std"]
                )
                global_mean = float(frame["measure"].mean())
                mean_variation = float(grouped["mean"].std())
                strength = mean_variation / (abs(global_mean) + 1e-9)
                if not math.isfinite(strength):
                    strength = 0.0

                samples = [
                    group["measure"].to_numpy()
                    for _, group in frame.groupby("dimension")
                    if len(group) > 1
                ]
                significance = None
                if len(samples) >= 2:
                    _, p_value = f_oneway(*samples)
                    if math.isfinite(float(p_value)):
                        significance = float(p_value)

                top_contributor = grouped["mean"].idxmax()
                evidence.append(
                    PairwiseEvidence(
                        dataset_id=dataset_id,
                        column_a=dimension.name,
                        column_b=measure.name,
                        rel_type="cat_num",
                        strength_score=float(min(abs(strength), 1.0)),
                        significance_score=significance,
                        evidence_data={
                            "group_means": {
                                str(key): float(value)
                                for key, value in grouped["mean"].items()
                            },
                            "top_contributor": str(top_contributor),
                        },
                    )
                )

        for index, first in enumerate(measures):
            for second in measures[index + 1 :]:
                frame = pd.DataFrame(
                    {
                        "first": pd.to_numeric(data[first.name], errors="coerce"),
                        "second": pd.to_numeric(data[second.name], errors="coerce"),
                    }
                ).dropna()
                if len(frame) < 2 or frame["first"].nunique() < 2 or frame["second"].nunique() < 2:
                    continue
                correlation, p_value = pearsonr(frame["first"], frame["second"])
                if not math.isfinite(float(correlation)) or abs(correlation) <= 0.3:
                    continue
                evidence.append(
                    PairwiseEvidence(
                        dataset_id=dataset_id,
                        column_a=first.name,
                        column_b=second.name,
                        rel_type="num_num",
                        strength_score=float(abs(correlation)),
                        significance_score=(
                            float(p_value) if math.isfinite(float(p_value)) else None
                        ),
                        evidence_data={"correlation": float(correlation)},
                    )
                )

        db.add_all(evidence)
        db.commit()
