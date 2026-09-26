import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_monitoring_insufficient_data(client):
    res = client.get("/api/v1/monitoring/status/expense_categorizer")
    assert res.status_code == 200
    data = res.json()
    assert data["feature_name"] == "expense_categorizer"
    assert data["baseline_health"]["health_status"] == "INSUFFICIENT_DATA"
    assert data["experiment_health"]["health_status"] == "INSUFFICIENT_DATA"
    assert data["alert_triggered"] is False

def test_monitoring_healthy_and_snapshot_history(client):
    # Setup feature flag
    flag = {
        "feature_name": "expense_categorizer",
        "enabled": True,
        "rollout_percentage": 50.0,
        "baseline_version": "categorizer_v1",
        "experiment_version": "categorizer_v2",
        "quality_threshold": 0.80
    }
    client.post("/api/v1/flags/", json=flag)

    # Seed good evaluations for Version B (categorizer_v2)
    eval1 = {
        "feature_name": "expense_categorizer",
        "version": "categorizer_v2",
        "user_id": "usr_1",
        "description": "Starbucks Coffee",
        "predicted_category": "Food & Dining",
        "expected_category": "Food & Dining",
        "confidence": 0.95
    }
    eval2 = {
        "feature_name": "expense_categorizer",
        "version": "categorizer_v2",
        "user_id": "usr_2",
        "description": "Uber Ride",
        "predicted_category": "Transportation",
        "expected_category": "Transportation",
        "confidence": 0.98
    }
    client.post("/api/v1/quality/evaluate", json=eval1)
    client.post("/api/v1/quality/evaluate", json=eval2)

    # Check live monitoring status
    res_status = client.get("/api/v1/monitoring/status/expense_categorizer")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["is_healthy"] is True
    assert status_data["alert_triggered"] is False
    assert status_data["experiment_health"]["health_status"] == "HEALTHY"
    assert status_data["experiment_health"]["sample_count"] == 2

    # Take snapshot
    res_snap = client.post("/api/v1/monitoring/snapshot/expense_categorizer")
    assert res_snap.status_code == 201
    assert len(res_snap.json()) >= 1

    # Check snapshot history
    res_hist = client.get("/api/v1/monitoring/history/expense_categorizer")
    assert res_hist.status_code == 200
    assert len(res_hist.json()) >= 1
    assert res_hist.json()[0]["health_status"] == "HEALTHY"

def test_monitoring_threshold_violated_alert(client):
    # Setup feature flag with high threshold 0.90
    flag = {
        "feature_name": "expense_categorizer",
        "enabled": True,
        "rollout_percentage": 50.0,
        "baseline_version": "categorizer_v1",
        "experiment_version": "categorizer_v2",
        "quality_threshold": 0.90
    }
    client.post("/api/v1/flags/", json=flag)

    # Seed bad evaluations for Version B (categorizer_v2) -> inaccurate predictions
    bad_eval1 = {
        "feature_name": "expense_categorizer",
        "version": "categorizer_v2",
        "user_id": "usr_bad_1",
        "description": "Laptop purchase",
        "predicted_category": "Food & Dining", # Inaccurate prediction!
        "expected_category": "Equipment",
        "confidence": 0.90
    }
    bad_eval2 = {
        "feature_name": "expense_categorizer",
        "version": "categorizer_v2",
        "user_id": "usr_bad_2",
        "description": "AWS cloud bill",
        "predicted_category": "Office Supplies", # Inaccurate prediction!
        "expected_category": "Software",
        "confidence": 0.85
    }
    client.post("/api/v1/quality/evaluate", json=bad_eval1)
    client.post("/api/v1/quality/evaluate", json=bad_eval2)

    # Query monitoring status -> Expect alert_triggered=True & THRESHOLD_VIOLATED
    res_status = client.get("/api/v1/monitoring/status/expense_categorizer")
    assert res_status.status_code == 200
    data = res_status.json()
    assert data["is_healthy"] is False
    assert data["alert_triggered"] is True
    assert data["experiment_health"]["health_status"] == "THRESHOLD_VIOLATED"
