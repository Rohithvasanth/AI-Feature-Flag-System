import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_gradual_rollout_staged_progression(client):
    # Step 1: Create feature flag starting at 0%
    flag = {
        "feature_name": "expense_categorizer",
        "enabled": True,
        "rollout_percentage": 0.0,
        "baseline_version": "categorizer_v1",
        "experiment_version": "categorizer_v2",
        "quality_threshold": 0.80
    }
    client.post("/api/v1/flags/", json=flag)

    # Step 2: Start gradual rollout -> Expect 10%
    res_start = client.post("/api/v1/rollout/start/expense_categorizer")
    assert res_start.status_code == 200
    assert res_start.json()["new_percentage"] == 10.0

    # Step 3: Seed good quality evaluation for Version B
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

    # Step 4: Advance stages sequentially: 10% -> 25% -> 50% -> 75% -> 100%
    res_25 = client.post("/api/v1/rollout/advance/expense_categorizer")
    assert res_25.json()["new_percentage"] == 25.0
    assert res_25.json()["action_taken"] == "ADVANCED"

    res_50 = client.post("/api/v1/rollout/advance/expense_categorizer")
    assert res_50.json()["new_percentage"] == 50.0

    res_75 = client.post("/api/v1/rollout/advance/expense_categorizer")
    assert res_75.json()["new_percentage"] == 75.0

    res_100 = client.post("/api/v1/rollout/advance/expense_categorizer")
    assert res_100.json()["new_percentage"] == 100.0
    assert res_100.json()["action_taken"] == "COMPLETED"

    # Step 5: Verify status endpoint
    res_status = client.get("/api/v1/rollout/status/expense_categorizer")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["current_percentage"] == 100.0
    assert status_data["is_completed"] is True
    assert status_data["is_healthy"] is True

    # Step 6: Verify history logs endpoint
    res_hist = client.get("/api/v1/rollout/history/expense_categorizer")
    assert res_hist.status_code == 200
    assert len(res_hist.json()) == 5

def test_rollout_blocked_and_rolled_back_on_threshold_violation(client):
    # Step 1: Create flag starting at 25% with threshold 0.85
    flag = {
        "feature_name": "expense_categorizer",
        "enabled": True,
        "rollout_percentage": 25.0,
        "baseline_version": "categorizer_v1",
        "experiment_version": "categorizer_v2",
        "quality_threshold": 0.85
    }
    client.post("/api/v1/flags/", json=flag)

    # Step 2: Seed bad evaluation for Version B (categorizer_v2)
    bad_eval = {
        "feature_name": "expense_categorizer",
        "version": "categorizer_v2",
        "user_id": "u_bad",
        "description": "Office Chair",
        "predicted_category": "Food & Dining", # Inaccurate prediction!
        "expected_category": "Equipment",
        "confidence": 0.90
    }
    client.post("/api/v1/quality/evaluate", json=bad_eval)

    # Step 3: Advance rollout -> Expect automatic rollback execution!
    res_adv = client.post("/api/v1/rollout/advance/expense_categorizer")
    assert res_adv.status_code == 200
    adv_data = res_adv.json()
    assert adv_data["action_taken"] == "ROLLED_BACK"
    assert adv_data["new_percentage"] == 0.0

    # Step 4: Verify feature flag in database updated to 0.0%
    flag_res = client.get("/api/v1/flags/expense_categorizer")
    assert flag_res.json()["rollout_percentage"] == 0.0
