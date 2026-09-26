import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.modules.ai_categorizer.service_v1 import CategorizerV1
from app.modules.ai_categorizer.service_v2 import CategorizerV2

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_version_a_categorizer_direct():
    v1 = CategorizerV1()
    res1 = v1.categorize("Starbucks Coffee #104", 5.50)
    assert res1.category == "Food & Dining"
    assert res1.assigned_version == "categorizer_v1"
    assert res1.confidence == 0.70

    res2 = v1.categorize("Uber Ride to airport", 34.00)
    assert res2.category == "Transportation"
    assert res2.assigned_version == "categorizer_v1"

def test_version_b_categorizer_direct():
    v2 = CategorizerV2()
    res1 = v2.categorize("Starbucks Coffee #104", 5.50)
    assert res1.category == "Food & Dining"
    assert res1.subcategory == "Coffee & Cafes"
    assert res1.assigned_version == "categorizer_v2"
    assert res1.confidence == 0.96

    res2 = v2.categorize("Uber Ride to airport", 34.00)
    assert res2.category == "Transportation"
    assert res2.subcategory == "Rideshare"
    assert res2.assigned_version == "categorizer_v2"

def test_categorizer_endpoint_fallback_when_flag_missing(client):
    payload = {
        "user_id": "user_fallback_1",
        "description": "Starbucks Latte",
        "amount": 4.75
    }
    response = client.post("/api/v1/categorize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["assigned_version"] == "categorizer_v1"
    assert data["is_experiment"] is False

def test_categorizer_feature_flag_routing(client):
    # Step 1: Create feature flag expense_categorizer with 50% rollout
    flag_payload = {
        "feature_name": "expense_categorizer",
        "enabled": True,
        "rollout_percentage": 50.0,
        "baseline_version": "categorizer_v1",
        "experiment_version": "categorizer_v2",
        "quality_threshold": 0.85
    }
    res_flag = client.post("/api/v1/flags/", json=flag_payload)
    assert res_flag.status_code == 201

    # Step 2: Categorize for a user assigned to Version A vs Version B
    # User 1 -> evaluate and route
    req1 = {"user_id": "user_test_99", "description": "AWS Cloud Hosting", "amount": 120.00}
    res1 = client.post("/api/v1/categorize", json=req1)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["assigned_version"] in ["categorizer_v1", "categorizer_v2"]

    # Step 3: Turn rollout to 100% -> ALL users must get Version B
    client.put("/api/v1/flags/expense_categorizer", json={"rollout_percentage": 100.0})
    res_100 = client.post("/api/v1/categorize", json=req1)
    assert res_100.status_code == 200
    data_100 = res_100.json()
    assert data_100["assigned_version"] == "categorizer_v2"
    assert data_100["is_experiment"] is True

    # Step 4: Turn rollout to 0% -> ALL users must get Version A
    client.put("/api/v1/flags/expense_categorizer", json={"rollout_percentage": 0.0})
    res_0 = client.post("/api/v1/categorize", json=req1)
    assert res_0.status_code == 200
    data_0 = res_0.json()
    assert data_0["assigned_version"] == "categorizer_v1"
    assert data_0["is_experiment"] is False
