"""
LUMYD Multilingual Narrative Generator
Synthesizes deterministic analytical computation results into clear, human-understandable
narrative explanations across English, Singlish, and Sinhala.
"""

from typing import Any, Dict, List
import re


class MultilingualNarrativeGenerator:
    SINGLISH_KEYWORDS = {
        "mcn", "machan", "ai", "kohomada", "adu", "une", "wadi", "karanna",
        "poddak", "kiyanna", "balanna", "ekai", "thiyenne", "mokakda",
        "monada", "dan", "ape", "eka", "kiyala", "neda", "drop", "une"
    }

    @classmethod
    def detect_language(cls, query: str) -> str:
        """Detects whether the query is Sinhala Unicode, Singlish, or English."""
        # 1. Check for Sinhala Unicode characters (\u0D80 - \u0DFF)
        if re.search(r"[\u0D80-\u0DFF]", query):
            return "sinhala"

        # 2. Check for Singlish transliteration tokens
        tokens = set(re.findall(r"\b\w+\b", query.lower()))
        singlish_hits = tokens.intersection(cls.SINGLISH_KEYWORDS)
        if len(singlish_hits) >= 1 or any("adu" in t or "une" in t for t in tokens):
            return "singlish"

        # 3. Default to English
        return "english"

    @classmethod
    def generate_narrative(
        cls, query: str, task_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates executive headline, conversational explanation, and key takeaways
        in the user's detected language.
        """
        lang = cls.detect_language(query)
        task = task_result.get("task", "ranking")

        if task == "ranking":
            return cls._narrate_ranking(task_result, lang)
        elif task == "comparison":
            return cls._narrate_comparison(task_result, lang)
        elif task == "root_cause":
            return cls._narrate_root_cause(task_result, lang)
        elif task == "trend":
            return cls._narrate_trend(task_result, lang)
        elif task == "distribution":
            return cls._narrate_distribution(task_result, lang)
        else:
            return cls._narrate_ranking(task_result, lang)

    # -------------------------------------------------------------
    # 1. RANKING NARRATIVE
    # -------------------------------------------------------------
    @classmethod
    def _narrate_ranking(cls, data: Dict[str, Any], lang: str) -> Dict[str, Any]:
        metric = data.get("metric", "Metric")
        dimension = data.get("dimension", "Category")
        top = data.get("top_entity") or {}
        bottom = data.get("bottom_entity") or {}
        top_name = top.get("entity", "Top Entity")
        top_val = f"{top.get('metric_value', 0):,}"
        top_share = top.get("share_pct", 0.0)
        bot_name = bottom.get("entity", "Bottom Entity")
        bot_val = f"{bottom.get('metric_value', 0):,}"
        total_entities = data.get("total_entities_analyzed", 0)
        avg_val = f"{data.get('average_per_entity', 0):,}"

        if lang == "singlish":
            headline = f"{dimension} walin '{top_name}' thama {metric} ranking eke #1 ({top_share}% share ekak ekka)."
            text = (
                f"{dimension} okkoma {total_entities} check karama, '{top_name}' thama lead karanne "
                f"total {metric} eka {top_val} ({top_share}% share) ganna gaman. "
                f"Anith athata '{bot_name}' thama aduma value eka aran thiyenne ({bot_val}). "
                f"Average per {dimension} eka {avg_val} ekka compare karaddi '{top_name}' godak issarahin inne."
            )
            takeaways = [
                f"#1 Thana: {top_name} ({top_val})",
                f"Market Share: {top_share}% overall volume eken",
                f"Average per {dimension}: {avg_val}",
            ]
        elif lang == "sinhala":
            headline = f"{dimension} අතරින් '{top_name}' {metric} අගයෙන් ප්‍රමුඛස්ථානය හිමිකරගෙන ඇත ({top_share}%). "
            text = (
                f"සමස්ත {dimension} කාණ්ඩ {total_entities} විශ්ලේෂණය කිරීමේදී, '{top_name}' ප්‍රමුඛස්ථානයේ පසුවන්නේ "
                f"මුළු {metric} අගය {top_val} ක් ({top_share}%) වාර්තා කරමිනි. "
                f"අඩුම අගය වාර්තා කර ඇත්තේ '{bot_name}' විසිනි ({bot_val})."
            )
            takeaways = [
                f"ප්‍රථම ස්ථානය: {top_name} ({top_val})",
                f"සමස්ත කොටස: {top_share}%",
                f"සාමාන්‍ය අගය: {avg_val}",
            ]
        else:  # english
            headline = f"'{top_name}' leads {metric} ranking with {top_share}% of total volume."
            text = (
                f"Across all {total_entities} analyzed {dimension} categories, '{top_name}' ranks #1 "
                f"with a cumulative {metric} of {top_val}, capturing {top_share}% of total performance. "
                f"In comparison, '{bot_name}' ranks lowest with {bot_val}. "
                f"The overall average across all {dimension} entities stands at {avg_val}."
            )
            takeaways = [
                f"Top Performer: {top_name} ({top_val})",
                f"Volume Share: {top_share}% of total",
                f"Category Average: {avg_val}",
            ]

        return {
            "headline": headline,
            "narrative_text": text,
            "key_takeaways": takeaways,
            "language_detected": lang,
        }

    # -------------------------------------------------------------
    # 2. COMPARISON NARRATIVE
    # -------------------------------------------------------------
    @classmethod
    def _narrate_comparison(cls, data: Dict[str, Any], lang: str) -> Dict[str, Any]:
        metric = data.get("metric", "Metric")
        ea = data.get("entity_a", {})
        eb = data.get("entity_b", {})
        winner = data.get("winner", "Entity")
        delta = f"{abs(data.get('delta', 0)):,}"
        pct = data.get("percentage_difference", 0.0)
        name_a, val_a = ea.get("name", "A"), f"{ea.get('value', 0):,}"
        name_b, val_b = eb.get("name", "B"), f"{eb.get('value', 0):,}"

        if lang == "singlish":
            headline = f"'{name_a}' ekai '{name_b}' ekai compare karaddi '{winner}' thama {delta} (+{abs(pct)}%) walin lead karanne."
            text = (
                f"Head-to-head baladdi, '{name_a}' total {metric} eka {val_a} wenawa, '{name_b}' total {metric} eka {val_b} wenawa. "
                f"Me deka athara gap eka {delta} ({abs(pct)}%). Overall '{winner}' thama wediyen perform karala thiyenne."
            )
            takeaways = [
                f"Winning Entity: {winner} (+{delta})",
                f"{name_a}: {val_a} vs {name_b}: {val_b}",
                f"Relative Difference: {abs(pct)}%",
            ]
        elif lang == "sinhala":
            headline = f"'{name_a}' සහ '{name_b}' අතර සංසන්දනයේදී '{winner}' {delta} කින් (+{abs(pct)}%) ඉදිරියෙන් සිටී."
            text = (
                f"සංසන්දනාත්මකව, '{name_a}' හි {metric} අගය {val_a} ක් වන අතර '{name_b}' හි අගය {val_b} කි. "
                f"ඒ අනුව '{winner}' ඉදිරියෙන් සිටින අතර වෙනස {delta} ක් වේ."
            )
            takeaways = [
                f"ඉදිරියෙන් සිටින පාර්ශවය: {winner} (+{delta})",
                f"{name_a}: {val_a} සහ {name_b}: {val_b}",
                f"වෙනස: {abs(pct)}%",
            ]
        else:  # english
            headline = f"'{winner}' outperforms '{name_b if winner == name_a else name_a}' in {metric} by {delta} (+{abs(pct)}%)."
            text = (
                f"In direct comparison, '{name_a}' generated {val_a} in {metric} versus {val_b} for '{name_b}'. "
                f"This represents a net performance delta of {delta} ({abs(pct)}% relative advantage) in favor of '{winner}'."
            )
            takeaways = [
                f"Lead Entity: {winner} (+{delta})",
                f"{name_a} ({val_a}) vs {name_b} ({val_b})",
                f"Performance Margin: {abs(pct)}%",
            ]

        return {
            "headline": headline,
            "narrative_text": text,
            "key_takeaways": takeaways,
            "language_detected": lang,
        }

    # -------------------------------------------------------------
    # 3. ROOT CAUSE NARRATIVE
    # -------------------------------------------------------------
    @classmethod
    def _narrate_root_cause(cls, data: Dict[str, Any], lang: str) -> Dict[str, Any]:
        metric = data.get("metric", "Metric")
        driver = data.get("primary_driver") or {}
        dim = driver.get("dimension", "Category")
        worst_cat = driver.get("underperforming_category", "N/A")
        worst_mean = f"{driver.get('underperforming_mean', 0):,}"
        top_cat = driver.get("top_performing_category", "N/A")
        top_mean = f"{driver.get('top_performing_mean', 0):,}"
        impact = driver.get("variance_impact_score", 0.0)

        if lang == "singlish":
            headline = f"{metric} drop/change ekata pradana hethuwa {dim} eke '{worst_cat}' underperform weema."
            text = (
                f"Variance breakdown eken penne {dim} dimension eken loku impact ekak wela thiyena bawa. "
                f"Visheshayenma '{worst_cat}' category eka adu average ekak ({worst_mean}) aran thiyenawa ({impact}% variance impact), "
                f"top-performing '{top_cat}' category eka {top_mean} gaddi. Me gap eka thama main deficit driver eka."
            )
            takeaways = [
                f"Primary Driver: {dim} -> '{worst_cat}'",
                f"Deficit Impact Score: {impact}%",
                f"Category Comparison: '{worst_cat}' ({worst_mean}) vs '{top_cat}' ({top_mean})",
            ]
        elif lang == "sinhala":
            headline = f"{metric} වෙනස්වීමට ප්‍රධාන සාධකය වන්නේ {dim} හි '{worst_cat}' දුර්වල වීමයි."
            text = (
                f"විශ්ලේෂණයට අනුව, {dim} කාණ්ඩයේ '{worst_cat}' හි අඩු ක්‍රියාකාරිත්වය ({worst_mean}) "
                f"සමස්ත {metric} අගයට විශාල බලපෑමක් ({impact}%) එල්ල කර ඇත."
            )
            takeaways = [
                f"ප්‍රධාන සාධකය: {dim} -> '{worst_cat}'",
                f"බලපෑම් ප්‍රතිශතය: {impact}%",
            ]
        else:  # english
            headline = f"Primary driver of {metric} variance identified in {dim}: '{worst_cat}'."
            text = (
                f"Variance decomposition reveals that fluctuations in {metric} are predominantly driven by "
                f"{dim}, specifically the '{worst_cat}' segment which exhibited a depressed average of {worst_mean} "
                f"({impact}% impact score) compared to top-performing '{top_cat}' at {top_mean}."
            )
            takeaways = [
                f"Primary Driver: {dim} -> '{worst_cat}'",
                f"Variance Impact: {impact}%",
                f"Benchmark: '{worst_cat}' ({worst_mean}) vs '{top_cat}' ({top_mean})",
            ]

        return {
            "headline": headline,
            "narrative_text": text,
            "key_takeaways": takeaways,
            "language_detected": lang,
        }

    # -------------------------------------------------------------
    # 4. TREND NARRATIVE
    # -------------------------------------------------------------
    @classmethod
    def _narrate_trend(cls, data: Dict[str, Any], lang: str) -> Dict[str, Any]:
        metric = data.get("metric", "Metric")
        time_dim = data.get("time_dimension", "Date")
        trajectory = data.get("trajectory", "Stable")
        overall_growth = data.get("overall_growth_pct", 0.0)
        peak = data.get("peak_period") or {}
        trough = data.get("trough_period") or {}
        peak_p, peak_v = peak.get("period", "N/A"), f"{peak.get('value', 0):,}"
        trough_p, trough_v = trough.get("period", "N/A"), f"{trough.get('value', 0):,}"

        if lang == "singlish":
            headline = f"{metric} time-series eka '{trajectory}' trajectory ekak pennanawa ({overall_growth}% overall growth)."
            text = (
                f"{time_dim} anuwa timeline eka baladdi, {metric} peak eka awilla thiyenne {peak_p} wala ({peak_v}). "
                f"Adu ma trough point eka thiyenne {trough_p} wala ({trough_v}). Overall performance eka {trajectory} widihata categorize wenawa."
            )
            takeaways = [
                f"Overall Trajectory: {trajectory} ({overall_growth}%)",
                f"Peak Period: {peak_p} ({peak_v})",
                f"Lowest Period: {trough_p} ({trough_v})",
            ]
        elif lang == "sinhala":
            headline = f"{time_dim} ඔස්සේ {metric} ප්‍රවණතාව '{trajectory}' තත්ත්වයක් පෙන්වයි ({overall_growth}%). "
            text = (
                f"කාලරාමුව තුළ {metric} උපරිම අගය {peak_p} හිදී ({peak_v}) සහ අවම අගය {trough_p} හිදී ({trough_v}) වාර්තා විය."
            )
            takeaways = [
                f"ප්‍රවණතාවය: {trajectory} ({overall_growth}%)",
                f"උපරිම කාලය: {peak_p} ({peak_v})",
                f"අවම කාලය: {trough_p} ({trough_v})",
            ]
        else:  # english
            headline = f"{metric} demonstrates an '{trajectory}' trajectory ({overall_growth}% net movement)."
            text = (
                f"Over the analyzed timeline across {time_dim}, {metric} reached its historic peak in {peak_p} ({peak_v}) "
                f"and touched its lowest level in {trough_p} ({trough_v}). The net trajectory is classified as {trajectory}."
            )
            takeaways = [
                f"Trend Direction: {trajectory} ({overall_growth}%)",
                f"Peak Point: {peak_p} ({peak_v})",
                f"Trough Point: {trough_p} ({trough_v})",
            ]

        return {
            "headline": headline,
            "narrative_text": text,
            "key_takeaways": takeaways,
            "language_detected": lang,
        }

    # -------------------------------------------------------------
    # 5. DISTRIBUTION NARRATIVE
    # -------------------------------------------------------------
    @classmethod
    def _narrate_distribution(cls, data: Dict[str, Any], lang: str) -> Dict[str, Any]:
        metric = data.get("metric", "Metric")
        mean_v = f"{data.get('mean', 0):,}"
        median_v = f"{data.get('median', 0):,}"
        min_v = f"{data.get('min_value', 0):,}"
        max_v = f"{data.get('max_value', 0):,}"
        outliers = data.get("outlier_count", 0)
        pareto = data.get("pareto_share_top_20pct", 0.0)

        if lang == "singlish":
            headline = f"{metric} distribution eke average eka {mean_v} saha median eka {median_v} ({outliers} outliers)."
            text = (
                f"{metric} values {min_v} idala {max_v} wenakan spread wela thiyenne. "
                f"Visheshayenma top 20% records walin total {metric} eken {pareto}% share ekak hold karanawa (Pareto effect). "
                f"Outlier count eka {outliers} kiyala detect wela thiyenawa."
            )
            takeaways = [
                f"Mean: {mean_v} vs Median: {median_v}",
                f"Spread: Range {min_v} to {max_v}",
                f"Pareto Concentration: Top 20% holds {pareto}% of total",
            ]
        elif lang == "sinhala":
            headline = f"{metric} ව්‍යාප්තියේ සාමාන්‍යය {mean_v} වන අතර මධ්‍යස්ථය {median_v} වේ (Outliers: {outliers})."
            text = (
                f"අගයන් {min_v} සිට {max_v} දක්වා විහිදෙන අතර ඉහළම 20% මඟින් සමස්තයෙන් {pareto}% ක් නියෝජනය වේ."
            )
            takeaways = [
                f"සාමාන්‍යය: {mean_v} | මධ්‍යස්ථය: {median_v}",
                f"පරාසය: {min_v} සිට {max_v}",
            ]
        else:  # english
            headline = f"{metric} distribution exhibits mean of {mean_v} and median of {median_v} ({outliers} outliers)."
            text = (
                f"Recorded values span from {min_v} to {max_v}. "
                f"Significant concentration was identified: the top 20% of entries account for {pareto}% of total aggregate volume. "
                f"A total of {outliers} statistical outliers were identified beyond 1.5x IQR boundaries."
            )
            takeaways = [
                f"Central Tendency: Mean {mean_v} | Median {median_v}",
                f"Span: {min_v} to {max_v}",
                f"Pareto Concentration: Top 20% accounts for {pareto}%",
            ]

        return {
            "headline": headline,
            "narrative_text": text,
            "key_takeaways": takeaways,
            "language_detected": lang,
        }
