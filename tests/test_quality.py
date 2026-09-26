import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.modules.quality.service import QualityEvaluationService

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_quality_score_calculation():
    service = QualityEvaluationService()
    
    # Accurate match with high confidence (0.95) -> 0.60 + 0.40*0.95 = 0.98
    score_accurate = service.calculate_quality_score(confidence=0.95, is_accurate=True)
    assert score_accurate == 0.98

    # Inaccurate match -> 0.20 * 0.90 = 0.18
    score_inaccurate = service.calculate_quality_score(confidence=0.90, is_accurate=False)
    assert score_inaccurate == 0.18

def test_record_and_summary_quality_api(client):
    # Record 2 evaluations for Version A (categorizer_v1)
    rec1 = {
        "feature_name": "expense_categorizer",
        "version": "categorizer_v1",
        "user_id": "usr_1",
        "description": "Starbucks Coffee",
        "predicted_category": "Food & Dining",
        "expected_category": "Food & Dining",
        "confidence": 0.70
    }
    rec2 = {
        "feature_name": "expense_categorizer",
        "version": "categorizer_v1",
        "user_id": "usr_2",
        "description": "Uber Ride",
        "predicted_category": "Transportation",
        "expected_category": "Software", # Inaccurate ground truth
        "confidence": 0.70
    }
    client.post("/api/v1/quality/evaluate", json=rec1)
    client.post("/api/v1/quality/evaluate", json=rec2)

    # Record 2 evaluations for Version B (categorizer_v2) - both accurate & high confidence
    rec3 = {
        "feature_name": "expense_categorizer",
        "version": "categorizer_v2",
        "user_id": "usr_3",
        "description": "Starbucks Coffee",
        "predicted_category": "Food & Dining",
        "expected_category": "Food & Dining",
        "confidence": 0.96
    }
    rec4 = {
        "feature_name": "expense_categorizer",
        "version": "categorizer_v2",
        "user_id": "usr_4",
        "description": "AWS Hosting",
        "predicted_category": "Software & Infrastructure",
        "expected_category": "Software & Infrastructure",
        "confidence": 0.98
    }
    client.post("/api/v1/quality/evaluate", json=rec3)
    client.post("/api/v1/quality/evaluate", json=rec4)

    # Get Summary Comparison
    res_summary = client.get("/api/v1/quality/summary/expense_categorizer")
    assert res_summary.status_code == 200
    data = res_summary.json()
    
    assert data["feature_name"] == "expense_categorizer"
    assert data["baseline_stats"]["version"] == "categorizer_v1"
    assert data["baseline_stats"]["total_evaluations"] == 2
    assert data["experiment_stats"]["version"] == "categorizer_v2"
    assert data["experiment_stats"]["total_evaluations"] == 2
    
    # Version B should win because higher accuracy and confidence
    assert data["winner_version"] == "categorizer_v2"
    assert data["quality_delta"] > 0.0
