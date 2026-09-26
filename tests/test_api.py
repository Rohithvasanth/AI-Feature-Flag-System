import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_create_feature_flag_api(client):
    payload = {
        "feature_name": "exp_categorizer",
        "enabled": True,
        "rollout_percentage": 50.0,
        "baseline_version": "v1.0",
        "experiment_version": "v2.0",
        "quality_threshold": 0.85
    }
    response = client.post("/api/v1/flags/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["feature_name"] == "exp_categorizer"
    assert data["enabled"] is True

def test_create_duplicate_flag_error(client):
    payload = {
        "feature_name": "dup_flag",
        "enabled": True,
        "rollout_percentage": 10.0,
        "baseline_version": "v1",
        "experiment_version": "v2",
        "quality_threshold": 0.8
    }
    client.post("/api/v1/flags/", json=payload)
    response = client.post("/api/v1/flags/", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_list_and_get_flags_api(client):
    flag1 = {
        "feature_name": "flag_1",
        "enabled": True,
        "rollout_percentage": 25.0,
        "baseline_version": "v1",
        "experiment_version": "v2",
        "quality_threshold": 0.8
    }
    client.post("/api/v1/flags/", json=flag1)
    
    # List flags
    res_list = client.get("/api/v1/flags/")
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1
    
    # Get flag
    res_get = client.get("/api/v1/flags/flag_1")
    assert res_get.status_code == 200
    assert res_get.json()["feature_name"] == "flag_1"

def test_get_non_existent_flag_404(client):
    res = client.get("/api/v1/flags/unknown_flag")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"]

def test_update_feature_flag_api(client):
    flag = {
        "feature_name": "update_flag",
        "enabled": False,
        "rollout_percentage": 10.0,
        "baseline_version": "v1",
        "experiment_version": "v2",
        "quality_threshold": 0.7
    }
    client.post("/api/v1/flags/", json=flag)
    
    update_payload = {"enabled": True, "rollout_percentage": 80.0}
    res_update = client.put("/api/v1/flags/update_flag", json=update_payload)
    assert res_update.status_code == 200
    updated_data = res_update.json()
    assert updated_data["enabled"] is True
    assert updated_data["rollout_percentage"] == 80.0

def test_delete_feature_flag_api(client):
    flag = {
        "feature_name": "delete_flag",
        "enabled": True,
        "rollout_percentage": 50.0,
        "baseline_version": "v1",
        "experiment_version": "v2",
        "quality_threshold": 0.8
    }
    client.post("/api/v1/flags/", json=flag)
    
    res_delete = client.delete("/api/v1/flags/delete_flag")
    assert res_delete.status_code == 200
    assert "deleted successfully" in res_delete.json()["message"]
    
    # Verify 404 after deletion
    assert client.get("/api/v1/flags/delete_flag").status_code == 404

def test_evaluate_flag_for_user_api(client):
    flag = {
        "feature_name": "ai_categorizer_api",
        "enabled": True,
        "rollout_percentage": 50.0,
        "baseline_version": "categorizer_v1",
        "experiment_version": "categorizer_v2",
        "quality_threshold": 0.85
    }
    client.post("/api/v1/flags/", json=flag)
    
    eval_payload = {"user_id": "usr_789"}
    res_eval = client.post("/api/v1/flags/ai_categorizer_api/evaluate", json=eval_payload)
    assert res_eval.status_code == 200
    eval_data = res_eval.json()
    assert eval_data["feature_name"] == "ai_categorizer_api"
    assert eval_data["user_id"] == "usr_789"
    assert eval_data["assigned_version"] in ["categorizer_v1", "categorizer_v2"]

def test_invalid_rollout_percentage_422(client):
    invalid_flag = {
        "feature_name": "invalid_flag",
        "enabled": True,
        "rollout_percentage": 150.0, # Exceeds 100.0
        "baseline_version": "v1",
        "experiment_version": "v2",
        "quality_threshold": 0.8
    }
    res = client.post("/api/v1/flags/", json=invalid_flag)
    assert res.status_code == 422
