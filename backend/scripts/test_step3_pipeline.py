import os
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from main import app
from app.database.session import SessionLocal
from app.models.agent import AgentTask, EscalationQueue

DATASET_ID = "d062c054-e008-48b9-9571-6e3dc1d502b6"

def run_step3_verification():
    client = TestClient(app)
    db = SessionLocal()

    print("=" * 70)
    print("STEP 3 VERIFICATION: SEMANTIC ROUTER + GEMINI FALLBACK + TRIAGE API")
    print("=" * 70)

    # -------------------------------------------------------------
    # TEST 1: Quota Status Endpoint
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing /api/v1/analyst/quota/status...")
    resp = client.get("/api/v1/analyst/quota/status")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    quota = resp.json()
    print(f"  Quota Status: {quota}")
    assert "requests_used_today" in quota or "daily_safety_limit" in quota
    print("  [PASS] Quota status endpoint verified.")

    # -------------------------------------------------------------
    # TEST 2: Local High-Confidence Route (Zero API Cost)
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Local High-Confidence Execution...")
    local_query = "top 5 regions by sales amount"
    resp = client.post(
        f"/api/v1/analyst/{DATASET_ID}/query",
        json={"query_text": local_query},
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    routing = data.get("routing_info", {})
    print(f"  Query: '{local_query}'")
    print(f"  Route: {routing.get('route')}, Confidence: {routing.get('confidence'):.4f}, Resolved By: {routing.get('resolved_by')}")
    print(f"  Intent: {data.get('structured_query', {}).get('intent')}")
    assert routing.get("route") == "AUTOMATED_EXECUTION"
    assert routing.get("resolved_by") == "local_router"
    assert routing.get("escalated") is False
    assert data.get("query_id", 0) > 0
    print("  [PASS] Local router executed in-distribution query with zero API cost.")

    # -------------------------------------------------------------
    # TEST 3: Out-of-Distribution Safe Escalation Receipt
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Out-of-Domain Escalation Receipt...")
    ood_query = "what is the capital of France and what is the weather like?"
    resp = client.post(
        f"/api/v1/analyst/{DATASET_ID}/query",
        json={"query_text": ood_query},
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    routing = data.get("routing_info", {})
    print(f"  Query: '{ood_query}'")
    print(f"  Route: {routing.get('route')}, Confidence: {routing.get('confidence'):.4f}, Resolved By: {routing.get('resolved_by')}")
    print(f"  Escalated: {routing.get('escalated')}")
    assert routing.get("route") == "HUMAN_ESCALATION"
    assert routing.get("escalated") is True
    escalation_id = data.get("evidence_package", {}).get("escalation_id")
    assert escalation_id is not None, "Expected escalation_id in evidence_package"
    print(f"  Escalation ID generated: {escalation_id}")
    print("  [PASS] Out-of-domain query safely escalated without breaking.")

    # -------------------------------------------------------------
    # TEST 4: Pending Escalations List
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing /api/v1/analyst/escalations/pending...")
    resp = client.get("/api/v1/analyst/escalations/pending")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    pending = resp.json()
    print(f"  Pending escalations count: {len(pending)}")
    matching = [item for item in pending if item["id"] == escalation_id]
    assert len(matching) > 0, f"Escalation {escalation_id} not found in pending list!"
    print(f"  Found pending escalation: ID {matching[0]['id']} - '{matching[0]['raw_query']}'")
    print("  [PASS] Pending escalation confirmed in triage queue.")

    # -------------------------------------------------------------
    # TEST 5: Manual Escalation Resolution & Active Learning Cache Re-warming
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Manual Escalation Resolution...")
    resolve_payload = {
        "escalation_id": escalation_id,
        "target_task_name": "ranking",
        "admin_notes": "Manually verified by admin test suite",
    }
    resp = client.post("/api/v1/analyst/escalations/resolve", json=resolve_payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    res_data = resp.json()
    print(f"  Resolution Response: {res_data}")

    # Verify DB state
    db.expire_all()
    esc_record = db.query(EscalationQueue).filter(EscalationQueue.id == escalation_id).first()
    assert esc_record.status == "RESOLVED"
    assert esc_record.resolved_task == "ranking"
    print(f"  Escalation DB Status: {esc_record.status}, Resolved Task: {esc_record.resolved_task}")

    task_record = db.query(AgentTask).filter(AgentTask.task_name == "ranking").first()
    assert ood_query in task_record.sample_queries
    print(f"  Sample queries for 'ranking' now count: {len(task_record.sample_queries)}")
    print("  [PASS] Manual resolution updated database and warmed router cache.")

    # Clean up test artifact from sample_queries so we don't pollute ranking with France weather
    task_record.sample_queries = [q for q in task_record.sample_queries if q != ood_query]
    db.commit()
    print("  [CLEANUP] Removed test OOD sample from ranking task.")

    # -------------------------------------------------------------
    # TEST 6: Automated Gemini Triage & Active Learning Re-warming
    # -------------------------------------------------------------
    print("\n[TEST 6] Testing Gemini Fallback for Ambiguous / Novel Query...")
    # A business query framed in informal phrasing that has low initial centroid similarity
    ambiguous_query = "machan poddak balanna Sales_Amount kohomada Region wise drop une kiyala"
    resp = client.post(
        f"/api/v1/analyst/{DATASET_ID}/query",
        json={"query_text": ambiguous_query},
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    routing = data.get("routing_info", {})
    print(f"  Query: '{ambiguous_query}'")
    print(f"  Route: {routing.get('route')}, Resolved By: {routing.get('resolved_by')}")
    print(f"  Intent: {data.get('structured_query', {}).get('intent')}")
    print(f"  Metric: {data.get('structured_query', {}).get('target_metric')}")
    print(f"  Dimensions: {data.get('structured_query', {}).get('dimensions')}")
    print(f"  Evidence Observations Count: {len(data.get('evidence_package', {}).get('observations', []))}")

    # Now verify that subsequent query hits local router!
    if routing.get("resolved_by") == "gemini_triage":
        print("\n  Closing Active Learning Loop: Querying same query again to verify local hit...")
        resp2 = client.post(
            f"/api/v1/analyst/{DATASET_ID}/query",
            json={"query_text": ambiguous_query},
        )
        routing2 = resp2.json().get("routing_info", {})
        print(f"  Second Run Route: {routing2.get('route')}, Resolved By: {routing2.get('resolved_by')}, Confidence: {routing2.get('confidence'):.4f}")
        assert routing2.get("resolved_by") == "local_router", "Expected local_router hit after active learning!"
        print("  [PASS] Online Active Learning successfully converted Gemini fallback into a permanent local hit!")

    print("\n" + "=" * 70)
    print("ALL STEP 3 PIPELINE TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    run_step3_verification()
