import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_rollback_no_action_when_healthy(client):
    flag = {
        "feature_name": "expense_categorizer",
        "enabled": True,
        "rollout_percentage": 50.0,
        "baseline_version": "categorizer_v1",
        "experiment_version": "categorizer_v2",
        "quality_threshold": 0.80
    }
    client.post("/api/v1/flags/", json=flag)

    # Good quality evaluation for categorizer_v2
    good_eval = {
        "feature_name": "expense_categorizer",
        "version": "categorizer_v2",
        "user_id": "u1",
        "description": "Starbucks Coffee",
        "predicted_category": "Food & Dining",
        "expected_category": "Food & Dining",
        "confidence": 0.95
    }
    client.post("/api/v1/quality/evaluate", json=good_eval)

    # Evaluate rollback -> Expect executed=False
    res = client.post("/api/v1/rollback/evaluate/expense_categorizer")
    assert res.status_code == 200
    data = res.json()
    assert data["executed"] is False
    assert "No rollback required" in data["reason"] or "satisfied" in data["reason"]

    # Verify flag rollout percentage remains 50%
    flag_res = client.get("/api/v1/flags/expense_categorizer")
    assert flag_res.json()["rollout_percentage"] == 50.0

def test_automatic_rollback_triggered_on_threshold_violated(client):
    # Step 1: Create flag with threshold 0.85 and 50% rollout
    flag = {
        "feature_name": "expense_categorizer",
        "enabled": True,
        "rollout_percentage": 50.0,
        "baseline_version": "categorizer_v1",
        "experiment_version": "categorizer_v2",
        "quality_threshold": 0.85
    }
    client.post("/api/v1/flags/", json=flag)

    # Step 2: Seed bad quality evaluations for Version B (categorizer_v2) -> inaccurate predictions
    bad_eval1 = {
        "feature_name": "expense_categorizer",
        "version": "categorizer_v2",
        "user_id": "u_bad_1",
        "description": "Laptop purchase",
        "predicted_category": "Food & Dining", # Inaccurate prediction!
        "expected_category": "Equipment",
        "confidence": 0.90
    }
    bad_eval2 = {
        "feature_name": "expense_categorizer",
        "version": "categorizer_v2",
        "user_id": "u_bad_2",
        "description": "AWS cloud bill",
        "predicted_category": "Office Supplies", # Inaccurate prediction!
        "expected_category": "Software",
        "confidence": 0.85
    }
    client.post("/api/v1/quality/evaluate", json=bad_eval1)
    client.post("/api/v1/quality/evaluate", json=bad_eval2)

    # Step 3: Trigger rollback evaluation -> Expect automatic rollback execution!
    res_rollback = client.post("/api/v1/rollback/evaluate/expense_categorizer")
    assert res_rollback.status_code == 200
    rb_data = res_rollback.json()
    assert rb_data["executed"] is True
    assert rb_data["previous_version"] == "categorizer_v2"
    assert rb_data["new_version"] == "categorizer_v1"
    assert rb_data["rollout_percentage_before"] == 50.0
    assert rb_data["rollout_percentage_after"] == 0.0

    # Step 4: Verify feature flag in database updated to rollout_percentage = 0.0
    flag_res = client.get("/api/v1/flags/expense_categorizer")
    assert flag_res.json()["rollout_percentage"] == 0.0

    # Step 5: Verify rollback event logged in history
    hist_res = client.get("/api/v1/rollback/history/expense_categorizer")
    assert hist_res.status_code == 200
    logs = hist_res.json()
    assert len(logs) == 1
    assert logs[0]["previous_version"] == "categorizer_v2"
    assert logs[0]["new_version"] == "categorizer_v1"

    # Step 6: Verify secondary call is idempotent (no second rollback)
    res_again = client.post("/api/v1/rollback/evaluate/expense_categorizer")
    assert res_again.json()["executed"] is False
    assert "already disabled or set to 0.0% rollout" in res_again.json()["reason"]
