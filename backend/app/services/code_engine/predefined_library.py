import re
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from app.services.narrative_generator import MultilingualNarrativeGenerator


class PredefinedCodeLibrary:
    """Predefined deterministic analytical routines for common business questions.

    Handles high-frequency queries locally with 0ms LLM latency and generates
    reusable Python code snippets.
    """

    @classmethod
    def find_best_numeric_column(cls, df: pd.DataFrame, preferred: Optional[str] = None) -> str:
        """Finds the most relevant numeric column in the dataframe."""
        if preferred and preferred in df.columns and pd.api.types.is_numeric_dtype(df[preferred]):
            return preferred

        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        for keyword in ["Sales", "Revenue", "Amount", "Total", "Price", "Cost", "Quantity"]:
            for col in numeric_cols:
                if keyword.lower() in col.lower():
                    return col
        return numeric_cols[0] if numeric_cols else df.columns[0]

    @classmethod
    def find_best_categorical_column(
        cls, df: pd.DataFrame, preferred: Optional[str] = None
    ) -> str:
        """Finds the most relevant categorical dimension in the dataframe."""
        if preferred and preferred in df.columns:
            return preferred

        cat_cols = [
            c
            for c in df.columns
            if not pd.api.types.is_numeric_dtype(df[c])
            and not pd.api.types.is_datetime64_any_dtype(df[c])
            and df[c].nunique() < 200
        ]
        for keyword in ["Product", "Category", "Region", "Rep", "Channel", "Type", "City"]:
            for col in cat_cols:
                if keyword.lower() in col.lower():
                    return col
        return cat_cols[0] if cat_cols else df.columns[0]

    @classmethod
    def match_and_generate(
        cls, query: str, df: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """Checks if the query matches a predefined common business task.

        Returns a dictionary with python_code, intent, and explanation if
        matched, or None if novel.
        """
        q = query.lower().strip()
        lang = MultilingualNarrativeGenerator.detect_language(query)

        # -------------------------------------------------------------
        # 1. SPECIFIC ENTITY / PRODUCT SALES LOOKUP
        # e.g., "what is the sales of Product_123", "Product_5 eke sales kiyada"
        # -------------------------------------------------------------
        cat_cols = [
            c
            for c in df.columns
            if not pd.api.types.is_numeric_dtype(df[c])
            and not pd.api.types.is_datetime64_any_dtype(df[c])
            and df[c].nunique() < 500
        ]

        # Scan for an exact or substring match of categorical values in query
        matched_entity: Optional[str] = None
        matched_col: Optional[str] = None

        for col in cat_cols:
            # Sample unique values
            uniques = df[col].dropna().unique()
            for uval in uniques:
                str_val = str(uval).strip()
                # Check if entity name with >= 3 chars appears as a token or word in query
                if len(str_val) >= 3 and re.search(rf"\b{re.escape(str_val.lower())}\b", q):
                    matched_entity = str_val
                    matched_col = col
                    break
            if matched_entity:
                break

        # Check if query asks for sales / lookup of this entity
        is_lookup_query = any(
            kw in q
            for kw in [
                "sale",
                "sales",
                "revenue",
                "amount",
                "how much",
                "kiyada",
                "kochcharada",
                "gana",
                "කොපමණ",
                "විකුණුම්",
            ]
        )

        if matched_entity and matched_col and (is_lookup_query or "what is" in q or "eke" in q):
            metric_col = cls.find_best_numeric_column(df)
            code = (
                f"# Filter dataframe for {matched_col} == '{matched_entity}' and calculate total {metric_col}\n"
                f"filtered_df = df[df['{matched_col}'].astype(str).str.lower() == '{matched_entity.lower()}']\n"
                f"result = {{\n"
                f"    'entity': '{matched_entity}',\n"
                f"    'dimension': '{matched_col}',\n"
                f"    'metric': '{metric_col}',\n"
                f"    'total_value': round(float(filtered_df['{metric_col}'].sum()), 2),\n"
                f"    'record_count': int(len(filtered_df)),\n"
                f"    'average_value': round(float(filtered_df['{metric_col}'].mean()), 2) if len(filtered_df) > 0 else 0.0\n"
                f"}}"
            )

            if lang == "singlish":
                explanation = f"'{matched_entity}' ({matched_col}) eke total {metric_col} eka ganan balala record count eka saha average value eka calculate kala."
            elif lang == "sinhala":
                explanation = f"'{matched_entity}' සඳහා සම්පූර්ණ {metric_col} අගය සහ සාමාන්‍ය ගණනය කරන ලදී."
            else:
                explanation = f"Computed the aggregate {metric_col} and transaction volume for '{matched_entity}' under dimension '{matched_col}'."

            return {
                "intent": "entity_lookup",
                "python_code": code,
                "explanation": explanation,
                "language": lang,
                "source": "predefined",
            }

        # -------------------------------------------------------------
        # 2. MOST / LEAST PROFITABLE OR BEST / WORST PERFORMER
        # e.g., "what is the most profitable product", "highest selling region"
        # -------------------------------------------------------------
        is_max = any(
            kw in q
            for kw in [
                "most",
                "highest",
                "best",
                "top",
                "maximum",
                "wadiyenma",
                "wadi",
                "ihalama",
                "වැඩිම",
                "ඉහළම",
            ]
        )
        is_min = any(
            kw in q
            for kw in [
                "least",
                "lowest",
                "worst",
                "bottom",
                "minimum",
                "aduma",
                "adu",
                "pahathma",
                "අඩුම",
                "පහළම",
            ]
        )

        if is_max or is_min:
            # Check if profitable is explicitly mentioned
            is_profit = any(kw in q for kw in ["profit", "profitable", "labadaayi", "ලාභ"])
            dim_col = cls.find_best_categorical_column(df)
            metric_col = cls.find_best_numeric_column(df)

            # Determine whether profit can be computed
            compute_profit = is_profit and "Unit_Cost" in df.columns and "Sales_Amount" in df.columns
            op = "idxmax()" if is_max else "idxmin()"
            superlative = "Highest / Most" if is_max else "Lowest / Least"
            superlative_sn = "Wadiyenma" if is_max else "Aduma"

            if compute_profit:
                code = (
                    f"# Compute profit per transaction and group by {dim_col}\n"
                    f"temp_df = df.copy()\n"
                    f"if 'Quantity_Sold' in temp_df.columns:\n"
                    f"    temp_df['Total_Profit'] = temp_df['Sales_Amount'] - (temp_df['Unit_Cost'] * temp_df['Quantity_Sold'])\n"
                    f"else:\n"
                    f"    temp_df['Total_Profit'] = temp_df['Sales_Amount'] - temp_df['Unit_Cost']\n"
                    f"grouped = temp_df.groupby('{dim_col}')['Total_Profit'].sum()\n"
                    f"best_entity = grouped.{op}\n"
                    f"best_val = grouped[best_entity]\n"
                    f"result = {{\n"
                    f"    'entity': str(best_entity),\n"
                    f"    'dimension': '{dim_col}',\n"
                    f"    'metric': 'Total_Profit',\n"
                    f"    'value': round(float(best_val), 2),\n"
                    f"    'rank_type': 'most_profitable' if {is_max} else 'least_profitable'\n"
                    f"}}"
                )
                metric_name = "Total Profit"
            else:
                code = (
                    f"# Group by {dim_col} and calculate sum of {metric_col}\n"
                    f"grouped = df.groupby('{dim_col}')['{metric_col}'].sum()\n"
                    f"best_entity = grouped.{op}\n"
                    f"best_val = grouped[best_entity]\n"
                    f"result = {{\n"
                    f"    'entity': str(best_entity),\n"
                    f"    'dimension': '{dim_col}',\n"
                    f"    'metric': '{metric_col}',\n"
                    f"    'value': round(float(best_val), 2),\n"
                    f"    'rank_type': '{'highest' if is_max else 'lowest'}'\n"
                    f"}}"
                )
                metric_name = metric_col

            if lang == "singlish":
                explanation = f"{dim_col} anuwa {superlative_sn} {metric_name} thiyena entity eka identify kala."
            elif lang == "sinhala":
                explanation = f"{dim_col} අනුව {metric_name} ඉහළම/පහළම අගය ගණනය කර හඳුනාගන්නා ලදී."
            else:
                explanation = f"Identified the {superlative.lower()} performing {dim_col} by {metric_name}."

            return {
                "intent": "extremum_analysis",
                "python_code": code,
                "explanation": explanation,
                "language": lang,
                "source": "predefined",
            }

        # -------------------------------------------------------------
        # 3. OVERALL TOTAL OR AVERAGE AGGREGATION
        # e.g., "what is the total sales", "average revenue"
        # -------------------------------------------------------------
        is_total = any(kw in q for kw in ["total", "sum", "overall", "mulu", "මුළු"])
        is_avg = any(kw in q for kw in ["average", "mean", "avg", "samanya", "සාමාන්‍ය"])
        is_grouped = any(kw in q for kw in ["wise", " by ", " per ", "group", "each", "anuwa", "අනුව"])

        if (is_total or is_avg) and not is_grouped:
            metric_col = cls.find_best_numeric_column(df)
            fn = "sum" if is_total else "mean"
            fn_title = "Total" if is_total else "Average"

            code = (
                f"# Calculate overall {fn_title.lower()} {metric_col}\n"
                f"result = {{\n"
                f"    'metric': '{metric_col}',\n"
                f"    'aggregation': '{fn_title}',\n"
                f"    'value': round(float(df['{metric_col}'].{fn}()), 2),\n"
                f"    'total_records': int(len(df))\n"
                f"}}"
            )

            if lang == "singlish":
                explanation = f"Mulu dataset eke {fn_title} {metric_col} eka calculate kala."
            elif lang == "sinhala":
                explanation = f"දත්ත ගොනුවේ {metric_col} හි සම්පූර්ණ අගය ගණනය කරන ලදී."
            else:
                explanation = f"Calculated the overall {fn_title.lower()} for {metric_col} across all records."

            return {
                "intent": "overall_aggregation",
                "python_code": code,
                "explanation": explanation,
                "language": lang,
                "source": "predefined",
            }

        return None
