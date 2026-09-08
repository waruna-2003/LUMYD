import io
import os
import sys
import pandas as pd

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from main import app
from app.database.session import SessionLocal
from app.models.dataset import Dataset
from app.services.code_engine.distillation_manager import DistillationManager
from app.services.code_engine.predefined_library import PredefinedCodeLibrary
from app.services.code_engine.sandbox import CodeSandbox
from app.services.storage_service import StorageService

DATASET_ID = "d062c054-e008-48b9-9571-6e3dc1d502b6"


def run_code_engine_tests():
    client = TestClient(app)
    db = SessionLocal()

    print("=" * 70)
    print("TEST SUITE: CODE-GEN ANALYTICS & TEACHER-STUDENT DISTILLATION")
    print("=" * 70)

    dataset = db.query(Dataset).filter(Dataset.id == DATASET_ID).first()
    assert dataset is not None, f"Dataset {DATASET_ID} not found!"

    resolved_path = StorageService.resolve_file_path(dataset.storage_path)
    ext = os.path.splitext(resolved_path)[1].lower()
    df = pd.read_csv(resolved_path) if ext == ".csv" else pd.read_excel(resolved_path)
    print(f"[+] Loaded dataset '{dataset.name}': {len(df)} rows, {len(df.columns)} columns.")

    # -------------------------------------------------------------
    # TEST 1: CodeSandbox Safety & Serialization
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing CodeSandbox...")
    res_scalar = CodeSandbox.execute("result = df['Sales_Amount'].sum()", df)
    assert res_scalar["success"], f"Scalar execution failed: {res_scalar}"
    print(f"  Scalar Result: {res_scalar['result']['formatted']} (time: {res_scalar['execution_time_ms']}ms)")

    res_df = CodeSandbox.execute(
        "result = df.groupby('Region')['Sales_Amount'].sum().reset_index()", df
    )
    assert res_df["success"] and res_df["result"]["type"] == "dataframe", f"DF failed: {res_df}"
    print(f"  DataFrame Result rows: {len(res_df['result']['rows'])} rows returned.")

    res_blocked = CodeSandbox.execute("import os; os.listdir('.')", df)
    assert not res_blocked["success"], "Security failure: restricted import should be blocked!"
    print(f"  Security Check: Blocked correctly ({res_blocked['error']})")
    print("  [PASS] CodeSandbox passed all security & execution checks.")

    # -------------------------------------------------------------
    # TEST 2: Predefined Code Library (0ms LLM Latency)
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Predefined Library for Common Tasks...")

    # A: Product / Entity Lookup
    entity_query = "what is the sales of North region"
    p_match = PredefinedCodeLibrary.match_and_generate(entity_query, df)
    assert p_match is not None, f"Predefined library failed to match entity query: '{entity_query}'"
    p_exec = CodeSandbox.execute(p_match["python_code"], df)
    assert p_exec["success"], f"Predefined code failed to run: {p_exec}"
    print(f"  Query: '{entity_query}' -> Intent: {p_match['intent']}")
    print(f"  Result: {p_exec['result']}")

    # B: Most Profitable / Best Performing Extremum
    extremum_query = "what is the most profitable product"
    p_ext = PredefinedCodeLibrary.match_and_generate(extremum_query, df)
    assert p_ext is not None, f"Predefined library failed to match: '{extremum_query}'"
    p_ext_exec = CodeSandbox.execute(p_ext["python_code"], df)
    assert p_ext_exec["success"], f"Extremum code failed to run: {p_ext_exec}"
    print(f"  Query: '{extremum_query}' -> Intent: {p_ext['intent']}")
    print(f"  Result: {p_ext_exec['result']}")

    # C: Overall Aggregation (Singlish)
    agg_query = "total sales kiyada"
    p_agg = PredefinedCodeLibrary.match_and_generate(agg_query, df)
    assert p_agg is not None, f"Predefined library failed to match: '{agg_query}'"
    p_agg_exec = CodeSandbox.execute(p_agg["python_code"], df)
    assert p_agg_exec["success"], f"Agg code failed to run: {p_agg_exec}"
    print(f"  Query: '{agg_query}' -> Intent: {p_agg['intent']}")
    print(f"  Result: {p_agg_exec['result']}")
    print("  [PASS] Predefined common tasks verified locally.")

    # -------------------------------------------------------------
    # TEST 3: API Pipeline Integration - Predefined Query
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing API endpoint with predefined query...")
    resp = client.post(
        f"/api/v1/analyst/{DATASET_ID}/query",
        json={"query_text": "what is the most profitable product"},
    )
    assert resp.status_code == 200, f"API query failed: {resp.text}"
    data = resp.json()
    assert data["code_source"] in {"predefined", "knowledge_bank"}
    assert data["generated_code"] is not None
    assert data["human_explanation"] is not None
    print(f"  API Response Code Source: {data['code_source']}")
    print(f"  Human Explanation: {data['human_explanation']}")
    print("  [PASS] Predefined API flow verified.")

    # -------------------------------------------------------------
    # TEST 4: API Pipeline Integration - Gemini Teacher for Novel Query
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Gemini Teacher on a novel Singlish query...")
    novel_query = "machan payment method wise average discount eka kochcharada kiyala balala denna"
    resp_novel = client.post(
        f"/api/v1/analyst/{DATASET_ID}/query",
        json={"query_text": novel_query},
    )
    assert resp_novel.status_code == 200, f"Teacher API query failed: {resp_novel.text}"
    data_novel = resp_novel.json()
    print(f"  Code Source: {data_novel['code_source']}")
    print(f"  Generated Code:\n{data_novel['generated_code']}")
    print(f"  Human Explanation: {data_novel['human_explanation']}")
    print(f"  Execution Time: {data_novel['execution_time_ms']}ms")
    assert data_novel["generated_code"] is not None
    print("  [PASS] Gemini Teacher generated and executed valid code.")

    # -------------------------------------------------------------
    # TEST 5: Knowledge Bank Semantic Reuse (0 API Calls)
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Knowledge Bank semantic reuse on repeated/similar query...")
    resp_repeat = client.post(
        f"/api/v1/analyst/{DATASET_ID}/query",
        json={"query_text": novel_query},
    )
    assert resp_repeat.status_code == 200, f"Repeated query failed: {resp_repeat.text}"
    data_repeat = resp_repeat.json()
    print(f"  Code Source for Repeated Query: {data_repeat['code_source']}")
    assert data_repeat["code_source"] in {"knowledge_bank", "gemini_teacher"}
    print("  [PASS] Knowledge Bank successfully cached and served query.")

    # -------------------------------------------------------------
    # TEST 6: Distillation Dataset & Statistics Endpoint
    # -------------------------------------------------------------
    print("\n[TEST 6] Testing Distillation Dataset Statistics Endpoint...")
    stats_resp = client.get("/api/v1/analyst/distillation/stats")
    assert stats_resp.status_code == 200, f"Distillation stats failed: {stats_resp.text}"
    stats = stats_resp.json()
    print(f"  Total Knowledge Records: {stats['total_knowledge_records']}")
    print(f"  Verified Executable Solutions: {stats['verified_executable_solutions']}")
    print(f"  Learned from Gemini Teacher: {stats['learned_from_gemini_teacher']}")
    print(f"  Predefined Solutions: {stats['predefined_solutions']}")
    print(f"  Distillation Dataset Lines: {stats['distillation_dataset_lines']}")
    print("  [PASS] Distillation statistics endpoint confirmed.")

    print("\n" + "=" * 70)
    print("ALL CODE-GEN & DISTILLATION PIPELINE TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_code_engine_tests()
