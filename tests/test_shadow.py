import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_enable_disable_shadow_mode_api(client):
    # Enable shadow mode
    res_enable = client.post("/api/v1/shadow/enable/expense_categorizer")
    assert res_enable.status_code == 200
    assert res_enable.json()["shadow_enabled"] is True

    # Check status
    res_status = client.get("/api/v1/shadow/status/expense_categorizer")
    assert res_status.status_code == 200
    assert res_status.json()["shadow_enabled"] is True

    # Disable shadow mode
    res_disable = client.post("/api/v1/shadow/disable/expense_categorizer")
    assert res_disable.status_code == 200
    assert res_disable.json()["shadow_enabled"] is False

def test_shadow_mode_zero_impact_on_production(client):
    # Step 1: Create feature flag with 0.0% rollout (Production assigned to categorizer_v1)
    flag_payload = {
        "feature_name": "expense_categorizer",
        "enabled": True,
        "rollout_percentage": 0.0,
        "baseline_version": "categorizer_v1",
        "experiment_version": "categorizer_v2",
        "quality_threshold": 0.85
    }
    client.post("/api/v1/flags/", json=flag_payload)

    # Step 2: Enable shadow mode for expense_categorizer
    client.post("/api/v1/shadow/enable/expense_categorizer")

    # Step 3: Send categorization request
    req = {
        "user_id": "user_shadow_test",
        "description": "Starbucks Coffee",
        "amount": 5.25
    }
    res = client.post("/api/v1/categorize", json=req)
    assert res.status_code == 200
    prod_data = res.json()

    # Step 4: Verify production response is 100% Version A (unaltered by shadow execution)
    assert prod_data["assigned_version"] == "categorizer_v1"
    assert prod_data["is_experiment"] is False
    assert prod_data["category"] == "Food & Dining"
    assert prod_data["subcategory"] == "Dining"

    # Step 5: Verify shadow comparison was recorded in background
    res_history = client.get("/api/v1/shadow/history/expense_categorizer")
    assert res_history.status_code == 200
    history_logs = res_history.json()
    assert len(history_logs) == 1

    shadow_log = history_logs[0]
    assert shadow_log["prod_version"] == "categorizer_v1"
    assert shadow_log["shadow_version"] == "categorizer_v2"
    assert shadow_log["prod_category"] == "Food & Dining"
    assert shadow_log["shadow_category"] == "Food & Dining"
    assert shadow_log["category_matched"] is True

def test_shadow_status_metrics(client):
    flag_payload = {
        "feature_name": "expense_categorizer",
        "enabled": True,
        "rollout_percentage": 0.0,
        "baseline_version": "categorizer_v1",
        "experiment_version": "categorizer_v2",
        "quality_threshold": 0.85
    }
    client.post("/api/v1/flags/", json=flag_payload)
    client.post("/api/v1/shadow/enable/expense_categorizer")

    # Perform 2 requests
    client.post("/api/v1/categorize", json={"user_id": "u1", "description": "Starbucks Coffee", "amount": 4.50})
    client.post("/api/v1/categorize", json={"user_id": "u2", "description": "Uber Ride", "amount": 25.00})

    res_status = client.get("/api/v1/shadow/status/expense_categorizer")
    assert res_status.status_code == 200
    status_data = res_status.json()

    assert status_data["shadow_enabled"] is True
    assert status_data["total_shadow_evaluations"] == 2
    assert status_data["category_match_rate"] == 100.0
    assert status_data["avg_prod_latency_ms"] >= 0.0
    assert status_data["avg_shadow_latency_ms"] >= 0.0
