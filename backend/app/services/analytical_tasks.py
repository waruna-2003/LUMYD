"""
LUMYD Analytical Task Execution Engine
Contains dedicated, deterministic execution functions for specific analytical tasks:
1. execute_ranking: Computes Top-K/Bottom-K, share %, and gap analysis.
2. execute_comparison: Head-to-head comparison between entities with category breakdowns.
3. execute_root_cause: Multi-factor variance decomposition identifying drivers of declines/spikes.
4. execute_trend: Chronological time-series breakdown, growth rates (MoM/QoQ), and trajectory.
5. execute_distribution: Statistical dispersion, quartiles, IQR outliers, and Pareto concentration.
"""

from typing import Any, Dict, List, Optional
import math
import numpy as np
import pandas as pd


class AnalyticalTaskEngine:
    @staticmethod
    def _clean_numeric_series(series: pd.Series) -> pd.Series:
        return pd.to_numeric(series, errors="coerce").fillna(0.0)

    @classmethod
    def execute_ranking(
        cls,
        df: pd.DataFrame,
        metric: str,
        dimension: str,
        top_k: int = 5,
        ascending: bool = False,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Computes Top-K or Bottom-K ranking for a metric across a dimension."""
        filtered_df = cls._apply_filters(df, filters)
        if metric not in filtered_df.columns or dimension not in filtered_df.columns:
            raise ValueError(f"Metric '{metric}' or Dimension '{dimension}' not found in dataset.")

        filtered_df[metric] = cls._clean_numeric_series(filtered_df[metric])

        # Group and aggregate
        grouped = (
            filtered_df.groupby(dimension, dropna=True)[metric]
            .agg(["sum", "mean", "count"])
            .reset_index()
        )
        grouped = grouped.sort_values(by="sum", ascending=ascending)

        total_sum = grouped["sum"].sum()
        mean_val = grouped["sum"].mean()

        table_data: List[Dict[str, Any]] = []
        cumulative = 0.0

        for idx, row in grouped.head(top_k).reset_index(drop=True).iterrows():
            val = float(row["sum"])
            share = (val / total_sum * 100.0) if total_sum > 0 else 0.0
            cumulative += share
            diff_from_mean = val - mean_val

            table_data.append({
                "rank": idx + 1,
                "entity": str(row[dimension]),
                "metric_value": round(val, 2),
                "metric_mean": round(float(row["mean"]), 2),
                "record_count": int(row["count"]),
                "share_pct": round(share, 1),
                "cumulative_share_pct": round(cumulative, 1),
                "diff_from_avg": round(diff_from_mean, 2),
            })

        top_entity = table_data[0] if table_data else None
        bottom_entity = (
            {
                "entity": str(grouped.iloc[-1][dimension]),
                "metric_value": round(float(grouped.iloc[-1]["sum"]), 2),
            }
            if not grouped.empty
            else None
        )

        return {
            "task": "ranking",
            "metric": metric,
            "dimension": dimension,
            "total_value": round(float(total_sum), 2),
            "average_per_entity": round(float(mean_val), 2),
            "top_entity": top_entity,
            "bottom_entity": bottom_entity,
            "table_data": table_data,
            "total_entities_analyzed": len(grouped),
        }

    @classmethod
    def execute_comparison(
        cls,
        df: pd.DataFrame,
        metric: str,
        dimension: str,
        entities: Optional[List[str]] = None,
        secondary_dimension: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compares specific entities (e.g., Colombo vs Kandy) on a target metric."""
        filtered_df = cls._apply_filters(df, filters)
        if metric not in filtered_df.columns or dimension not in filtered_df.columns:
            raise ValueError(f"Metric '{metric}' or Dimension '{dimension}' not found in dataset.")

        filtered_df[metric] = cls._clean_numeric_series(filtered_df[metric])

        # If entities not specified, take top 2 by sum
        if not entities or len(entities) < 2:
            top_2 = (
                filtered_df.groupby(dimension)[metric]
                .sum()
                .nlargest(2)
                .index.tolist()
            )
            entities = [str(e) for e in top_2]

        entity_a_name = str(entities[0])
        entity_b_name = str(entities[1])

        df_a = filtered_df[filtered_df[dimension].astype(str).str.lower() == entity_a_name.lower()]
        df_b = filtered_df[filtered_df[dimension].astype(str).str.lower() == entity_b_name.lower()]

        val_a = float(df_a[metric].sum())
        val_b = float(df_b[metric].sum())

        delta = val_a - val_b
        pct_diff = ((val_a - val_b) / val_b * 100.0) if val_b != 0 else (100.0 if val_a > 0 else 0.0)

        winner = entity_a_name if val_a >= val_b else entity_b_name
        winner_margin = abs(delta)

        # Secondary breakdown if a secondary categorical dimension exists
        breakdown_data: List[Dict[str, Any]] = []
        if secondary_dimension and secondary_dimension in filtered_df.columns:
            sec_a = df_a.groupby(secondary_dimension)[metric].sum().to_dict()
            sec_b = df_b.groupby(secondary_dimension)[metric].sum().to_dict()
            all_categories = set(sec_a.keys()) | set(sec_b.keys())

            for cat in all_categories:
                ca_val = float(sec_a.get(cat, 0.0))
                cb_val = float(sec_b.get(cat, 0.0))
                cat_delta = ca_val - cb_val
                breakdown_data.append({
                    "category": str(cat),
                    "entity_a_val": round(ca_val, 2),
                    "entity_b_val": round(cb_val, 2),
                    "delta": round(cat_delta, 2),
                })
            breakdown_data.sort(key=lambda x: abs(x["delta"]), reverse=True)

        return {
            "task": "comparison",
            "metric": metric,
            "dimension": dimension,
            "entity_a": {
                "name": entity_a_name,
                "value": round(val_a, 2),
                "record_count": len(df_a),
            },
            "entity_b": {
                "name": entity_b_name,
                "value": round(val_b, 2),
                "record_count": len(df_b),
            },
            "delta": round(delta, 2),
            "percentage_difference": round(pct_diff, 1),
            "winner": winner,
            "winner_margin": round(winner_margin, 2),
            "breakdown": breakdown_data[:5],
        }

    @classmethod
    def execute_root_cause(
        cls,
        df: pd.DataFrame,
        metric: str,
        target_dimension: Optional[str] = None,
        target_value: Optional[str] = None,
        secondary_dimensions: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Diagnoses why a metric underperformed or dropped by decomposing variance across drivers."""
        filtered_df = cls._apply_filters(df, filters)
        if metric not in filtered_df.columns:
            raise ValueError(f"Metric '{metric}' not found in dataset.")

        filtered_df[metric] = cls._clean_numeric_series(filtered_df[metric])

        # Find categorical candidate dimensions for driver breakdown
        candidate_dims = secondary_dimensions or [
            col
            for col in filtered_df.columns
            if not pd.api.types.is_numeric_dtype(filtered_df[col])
            and not pd.api.types.is_datetime64_any_dtype(filtered_df[col])
            and col not in {target_dimension or ""}
            and filtered_df[col].nunique() < 30
        ]

        # Overall baseline
        overall_mean = float(filtered_df[metric].mean())
        overall_total = float(filtered_df[metric].sum())

        driver_findings: List[Dict[str, Any]] = []

        for dim in candidate_dims[:4]:
            grouped = (
                filtered_df.groupby(dim)[metric]
                .agg(["sum", "mean", "count", "std"])
                .reset_index()
            )
            dim_total = grouped["sum"].sum()
            if dim_total == 0:
                continue

            # Identify category with largest deficit or variance from expected share
            expected_share = 1.0 / len(grouped) if len(grouped) > 0 else 1.0
            grouped["share"] = grouped["sum"] / dim_total
            grouped["deficit"] = (expected_share - grouped["share"]).clip(lower=0.0)

            # Sort by lowest mean or highest deficit
            worst_row = grouped.sort_values(by="mean", ascending=True).iloc[0]
            best_row = grouped.sort_values(by="mean", ascending=False).iloc[0]

            impact_pct = round(float(worst_row["deficit"]) * 100.0, 1)
            driver_findings.append({
                "dimension": dim,
                "underperforming_category": str(worst_row[dim]),
                "underperforming_mean": round(float(worst_row["mean"]), 2),
                "underperforming_sum": round(float(worst_row["sum"]), 2),
                "top_performing_category": str(best_row[dim]),
                "top_performing_mean": round(float(best_row["mean"]), 2),
                "variance_impact_score": impact_pct,
            })

        driver_findings.sort(key=lambda x: x["variance_impact_score"], reverse=True)
        primary_driver = driver_findings[0] if driver_findings else None

        return {
            "task": "root_cause",
            "metric": metric,
            "overall_total": round(overall_total, 2),
            "overall_mean": round(overall_mean, 2),
            "primary_driver": primary_driver,
            "contributing_factors": driver_findings,
        }

    @classmethod
    def execute_trend(
        cls,
        df: pd.DataFrame,
        metric: str,
        time_dimension: Optional[str] = None,
        granularity: str = "auto",
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Calculates chronological trajectory, growth rates, and inflection points."""
        filtered_df = cls._apply_filters(df, filters)
        if metric not in filtered_df.columns:
            raise ValueError(f"Metric '{metric}' not found in dataset.")

        # Find time dimension if not specified
        if not time_dimension:
            time_candidates = [
                col for col in filtered_df.columns
                if "date" in col.lower() or "time" in col.lower() or "year" in col.lower() or "month" in col.lower()
            ]
            time_dimension = time_candidates[0] if time_candidates else filtered_df.columns[0]

        filtered_df[metric] = cls._clean_numeric_series(filtered_df[metric])

        # Attempt datetime parse
        try:
            filtered_df["_dt"] = pd.to_datetime(filtered_df[time_dimension], errors="coerce")
            filtered_df = filtered_df.dropna(subset=["_dt"]).sort_values(by="_dt")
            # Group by Month or Quarter
            grouped = (
                filtered_df.set_index("_dt")
                .resample("ME")[metric]
                .agg(["sum", "count"])
                .reset_index()
            )
            grouped["period_label"] = grouped["_dt"].dt.strftime("%Y-%m")
        except Exception:
            # Fallback: group by raw categorical order
            grouped = (
                filtered_df.groupby(time_dimension)[metric]
                .agg(["sum", "count"])
                .reset_index()
            )
            grouped["period_label"] = grouped[time_dimension].astype(str)

        # Compute period-over-period growth
        grouped["prev_sum"] = grouped["sum"].shift(1)
        grouped["growth_pct"] = (
            (grouped["sum"] - grouped["prev_sum"]) / grouped["prev_sum"] * 100.0
        ).fillna(0.0)

        timeline: List[Dict[str, Any]] = []
        for _, row in grouped.iterrows():
            timeline.append({
                "period": str(row["period_label"]),
                "value": round(float(row["sum"]), 2),
                "growth_pct": round(float(row["growth_pct"]), 1),
                "record_count": int(row["count"]),
            })

        if len(timeline) >= 2:
            first_val = timeline[0]["value"]
            last_val = timeline[-1]["value"]
            overall_growth = ((last_val - first_val) / first_val * 100.0) if first_val != 0 else 0.0

            if overall_growth > 5.0:
                trajectory = "Upward Growth"
            elif overall_growth < -5.0:
                trajectory = "Downward Decline"
            else:
                trajectory = "Stable / Flat"
        else:
            overall_growth = 0.0
            trajectory = "Insufficient time periods"

        peak = max(timeline, key=lambda x: x["value"]) if timeline else None
        trough = min(timeline, key=lambda x: x["value"]) if timeline else None

        return {
            "task": "trend",
            "metric": metric,
            "time_dimension": time_dimension,
            "trajectory": trajectory,
            "overall_growth_pct": round(overall_growth, 1),
            "peak_period": peak,
            "trough_period": trough,
            "timeline": timeline,
        }

    @classmethod
    def execute_distribution(
        cls,
        df: pd.DataFrame,
        metric: str,
        dimension: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Calculates statistical spread, quartiles, outliers, and Pareto concentration."""
        filtered_df = cls._apply_filters(df, filters)
        if metric not in filtered_df.columns:
            raise ValueError(f"Metric '{metric}' not found in dataset.")

        clean_series = cls._clean_numeric_series(filtered_df[metric]).dropna()

        count = int(len(clean_series))
        min_v = float(clean_series.min()) if count > 0 else 0.0
        max_v = float(clean_series.max()) if count > 0 else 0.0
        mean_v = float(clean_series.mean()) if count > 0 else 0.0
        median_v = float(clean_series.median()) if count > 0 else 0.0
        std_v = float(clean_series.std()) if count > 1 else 0.0

        q1 = float(clean_series.quantile(0.25)) if count > 0 else 0.0
        q3 = float(clean_series.quantile(0.75)) if count > 0 else 0.0
        iqr = q3 - q1

        # Outlier count (1.5 * IQR)
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = clean_series[(clean_series < lower_bound) | (clean_series > upper_bound)]

        # Pareto Concentration
        sorted_s = clean_series.sort_values(ascending=False)
        top_20_pct_count = max(1, int(count * 0.20))
        top_20_sum = sorted_s.head(top_20_pct_count).sum()
        total_sum = sorted_s.sum()
        pareto_share = (top_20_sum / total_sum * 100.0) if total_sum > 0 else 0.0

        return {
            "task": "distribution",
            "metric": metric,
            "total_records": count,
            "mean": round(mean_v, 2),
            "median": round(median_v, 2),
            "std_dev": round(std_v, 2),
            "min_value": round(min_v, 2),
            "max_value": round(max_v, 2),
            "q1_25pct": round(q1, 2),
            "q3_75pct": round(q3, 2),
            "iqr": round(iqr, 2),
            "outlier_count": len(outliers),
            "pareto_share_top_20pct": round(pareto_share, 1),
        }

    @staticmethod
    def _apply_filters(df: pd.DataFrame, filters: Optional[Dict[str, Any]]) -> pd.DataFrame:
        if not filters:
            return df.copy()
        res = df.copy()
        for col, val in filters.items():
            if col in res.columns:
                res = res[res[col].astype(str).str.lower() == str(val).lower()]
        return res
