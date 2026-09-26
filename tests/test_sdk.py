import pytest
from fastapi.testclient import TestClient
from app.main import app
from sdk import FeatureFlagClient, FeatureFlagNotFoundError, FeatureFlagServerError

@pytest.fixture
def sdk_client():
    test_http_client = TestClient(app)
    sdk = FeatureFlagClient(custom_client=test_http_client)
    yield sdk
    sdk.close()

def test_sdk_evaluate_flag(sdk_client):
    test_http_client = TestClient(app)
    flag_payload = {
        "feature_name": "expense_categorizer_v2",
        "enabled": True,
        "rollout_percentage": 50.0,
        "baseline_version": "categorizer_v1",
        "experiment_version": "categorizer_v2",
        "quality_threshold": 0.85
    }
    res = test_http_client.post("/api/v1/flags/", json=flag_payload)
    assert res.status_code == 201

    eval_result = sdk_client.evaluate("expense_categorizer_v2", "user_123")
    assert eval_result.feature_name == "expense_categorizer_v2"
    assert eval_result.user_id == "user_123"
    assert eval_result.assigned_version in ["categorizer_v1", "categorizer_v2"]

def test_sdk_get_and_list_flags(sdk_client):
    test_http_client = TestClient(app)
    flag_payload = {
        "feature_name": "sdk_test_flag",
        "enabled": True,
        "rollout_percentage": 100.0,
        "baseline_version": "v1",
        "experiment_version": "v2",
        "quality_threshold": 0.8
    }
    test_http_client.post("/api/v1/flags/", json=flag_payload)

    flag = sdk_client.get_flag("sdk_test_flag")
    assert flag.feature_name == "sdk_test_flag"
    assert flag.rollout_percentage == 100.0

    all_flags = sdk_client.list_flags()
    assert len(all_flags) >= 1
    assert any(f.feature_name == "sdk_test_flag" for f in all_flags)

def test_sdk_missing_flag_raises_404_error(sdk_client):
    with pytest.raises(FeatureFlagNotFoundError) as exc_info:
        sdk_client.evaluate("missing_sdk_flag", "user_123")
    assert "not found" in str(exc_info.value)

def test_sdk_context_manager():
    test_http_client = TestClient(app)
    with FeatureFlagClient(custom_client=test_http_client) as client:
        flags = client.list_flags()
        assert isinstance(flags, list)

def test_sdk_connection_error():
    dead_client = FeatureFlagClient(base_url="http://127.0.0.1:59999", timeout=0.1)
    with pytest.raises(FeatureFlagServerError):
        dead_client.evaluate("any_flag", "user_1")
    dead_client.close()
