import os
import sys
import io
import pandas as pd

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from app.database.session import SessionLocal
from app.models.dataset import Dataset
from app.services.analytical_tasks import AnalyticalTaskEngine
from app.services.narrative_generator import MultilingualNarrativeGenerator

DATASET_ID = "d062c054-e008-48b9-9571-6e3dc1d502b6"

def test_tasks():
    db = SessionLocal()
    dataset = db.query(Dataset).filter(Dataset.id == DATASET_ID).first()
    assert dataset is not None, "Dataset not found!"

    from app.services.storage_service import StorageService
    resolved_path = StorageService.resolve_file_path(dataset.storage_path)
    ext = os.path.splitext(resolved_path)[1].lower()
    df = pd.read_csv(resolved_path) if ext == ".csv" else pd.read_excel(resolved_path)
    print(f"Loaded dataset: {dataset.name}, rows: {len(df)}, columns: {list(df.columns)}")

    print("\n" + "=" * 60)
    print("TEST 1: EXECUTE RANKING")
    print("=" * 60)
    res_ranking = AnalyticalTaskEngine.execute_ranking(df, metric="Sales_Amount", dimension="Region", top_k=5)
    print(f"Total: {res_ranking['total_value']}, Top: {res_ranking['top_entity']['entity']} ({res_ranking['top_entity']['share_pct']}%)")
    narrative_en = MultilingualNarrativeGenerator.generate_narrative("top regions by sales amount", res_ranking)
    narrative_si = MultilingualNarrativeGenerator.generate_narrative("sales wedima region monada mcn", res_ranking)
    print(f"  [EN Headline]: {narrative_en['headline']}")
    print(f"  [EN Narrative]: {narrative_en['narrative_text']}")
    print(f"  [Singlish Headline]: {narrative_si['headline']}")
    print(f"  [Singlish Narrative]: {narrative_si['narrative_text']}")
    assert res_ranking["top_entity"] is not None

    print("\n" + "=" * 60)
    print("TEST 2: EXECUTE COMPARISON")
    print("=" * 60)
    res_comp = AnalyticalTaskEngine.execute_comparison(df, metric="Sales_Amount", dimension="Region")
    print(f"Winner: {res_comp['winner']} by {res_comp['winner_margin']} ({res_comp['percentage_difference']}%)")
    narrative_comp = MultilingualNarrativeGenerator.generate_narrative("regions dekak compare karanna", res_comp)
    print(f"  [Singlish Headline]: {narrative_comp['headline']}")
    print(f"  [Singlish Narrative]: {narrative_comp['narrative_text']}")
    assert res_comp["winner"] is not None

    print("\n" + "=" * 60)
    print("TEST 3: EXECUTE ROOT CAUSE")
    print("=" * 60)
    res_rc = AnalyticalTaskEngine.execute_root_cause(df, metric="Sales_Amount", target_dimension="Region")
    print(f"Primary driver: {res_rc['primary_driver']}")
    narrative_rc = MultilingualNarrativeGenerator.generate_narrative("sales drop une ai kiyala kiyanna", res_rc)
    print(f"  [Singlish Headline]: {narrative_rc['headline']}")
    print(f"  [Singlish Narrative]: {narrative_rc['narrative_text']}")
    assert res_rc["primary_driver"] is not None

    print("\n" + "=" * 60)
    print("TEST 4: EXECUTE TREND")
    print("=" * 60)
    res_trend = AnalyticalTaskEngine.execute_trend(df, metric="Sales_Amount", time_dimension="Sale_Date")
    print(f"Trajectory: {res_trend['trajectory']}, Periods: {len(res_trend['timeline'])}")
    narrative_trend = MultilingualNarrativeGenerator.generate_narrative("sales trend eka kohomada", res_trend)
    print(f"  [Singlish Headline]: {narrative_trend['headline']}")
    print(f"  [Singlish Narrative]: {narrative_trend['narrative_text']}")
    assert len(res_trend["timeline"]) > 0

    print("\n" + "=" * 60)
    print("TEST 5: EXECUTE DISTRIBUTION")
    print("=" * 60)
    res_dist = AnalyticalTaskEngine.execute_distribution(df, metric="Sales_Amount")
    print(f"Mean: {res_dist['mean']}, Median: {res_dist['median']}, Pareto Top 20%: {res_dist['pareto_share_top_20pct']}%")
    narrative_dist = MultilingualNarrativeGenerator.generate_narrative("sales distribution eka pennanna", res_dist)
    print(f"  [Singlish Headline]: {narrative_dist['headline']}")
    print(f"  [Singlish Narrative]: {narrative_dist['narrative_text']}")
    assert res_dist["total_records"] > 0

    print("\n" + "=" * 60)
    print("ALL ANALYTICAL ENGINE TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    test_tasks()
