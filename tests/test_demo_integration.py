import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_system_demo_lifecycle():
    """
    End-to-End integration test covering Modules 1 through 13:
    1. Feature Flag creation & evaluation
    2. Consistent user assignment & AI Expense Categorizer routing
    3. Shadow Mode activation and non-intrusive dual evaluation
    4. Quality score logging & degradation detection
    5. Automatic Rollback trigger on threshold violation
    6. Gradual Rollout Controller progression
    7. Dashboard endpoint rendering
    """
    feature_name = "expense_categorizer"

    # Step 1: Create Feature Flag (returns 201 Created)
    create_res = client.post("/api/v1/flags/", json={
        "feature_name": feature_name,
        "description": "AI Expense Categorizer Demo Flag",
        "enabled": True,
        "baseline_version": "categorizer_v1",
        "experiment_version": "categorizer_v2",
        "rollout_percentage": 50.0,
        "quality_threshold": 0.85
    })
    assert create_res.status_code == 201
    flag_data = create_res.json()
    assert flag_data["feature_name"] == feature_name
    assert flag_data["rollout_percentage"] == 50.0

    # Step 2: Categorization with consistent assignment
    resp_user1 = client.post("/api/v1/categorize", json={
        "user_id": "user_100",
        "amount": 45.50,
        "merchant": "Starbucks Coffee",
        "description": "Morning coffee"
    })
    assert resp_user1.status_code == 200
    res1_body = resp_user1.json()
    assert "category" in res1_body
    assert res1_body["assigned_version"] in ["categorizer_v1", "categorizer_v2"]

    # Step 3: Enable Shadow Mode
    shadow_enable = client.post(f"/api/v1/shadow/enable/{feature_name}")
    assert shadow_enable.status_code == 200
    assert shadow_enable.json()["shadow_enabled"] is True

    # Execute categorization under Shadow Mode
    resp_shadow = client.post("/api/v1/categorize", json={
        "user_id": "user_200",
        "amount": 1200.00,
        "merchant": "Apple Store",
        "description": "New iPad"
    })
    assert resp_shadow.status_code == 200

    # Check shadow comparison metrics
    shadow_metrics = client.get(f"/api/v1/shadow/status/{feature_name}")
    assert shadow_metrics.status_code == 200
    assert shadow_metrics.json()["shadow_enabled"] is True
    assert shadow_metrics.json()["total_shadow_evaluations"] >= 1

    # Step 4: Record inaccurate quality score for Version B to trigger threshold violation
    bad_eval1 = {
        "feature_name": feature_name,
        "version": "categorizer_v2",
        "user_id": "u_bad_1",
        "description": "Laptop purchase",
        "predicted_category": "Food & Dining",
        "expected_category": "Equipment",
        "confidence": 0.90
    }
    bad_eval2 = {
        "feature_name": feature_name,
        "version": "categorizer_v2",
        "user_id": "u_bad_2",
        "description": "AWS cloud bill",
        "predicted_category": "Office Supplies",
        "expected_category": "Software",
        "confidence": 0.85
    }
    client.post("/api/v1/quality/evaluate", json=bad_eval1)
    client.post("/api/v1/quality/evaluate", json=bad_eval2)

    # Step 5: Evaluate Monitoring Status
    mon_res = client.get(f"/api/v1/monitoring/status/{feature_name}")
    assert mon_res.status_code == 200
    mon_data = mon_res.json()
    assert mon_data["is_healthy"] is False
    assert mon_data["alert_triggered"] is True
    assert mon_data["experiment_health"]["health_status"] == "THRESHOLD_VIOLATED"

    # Step 6: Trigger Automatic Rollback Evaluation
    rollback_res = client.post(f"/api/v1/rollback/evaluate/{feature_name}")
    assert rollback_res.status_code == 200
    rb_data = rollback_res.json()
    assert rb_data["executed"] is True
    assert rb_data["rollout_percentage_after"] == 0.0
    assert rb_data["new_version"] == "categorizer_v1"

    # Verify Flag is rolled back to 0.0%
    flag_after_rb = client.get(f"/api/v1/flags/{feature_name}").json()
    assert flag_after_rb["rollout_percentage"] == 0.0

    # Step 7: Seed multiple accurate evaluations for Version B so average quality recovers > 0.85
    for i in range(20):
        good_eval = {
            "feature_name": feature_name,
            "version": "categorizer_v2",
            "user_id": f"u_good_{i}",
            "description": "Starbucks Coffee",
            "predicted_category": "Food & Dining",
            "expected_category": "Food & Dining",
            "confidence": 0.95
        }
        client.post("/api/v1/quality/evaluate", json=good_eval)

    # Start Rollout (sets percentage to 10%)
    start_rollout = client.post(f"/api/v1/rollout/start/{feature_name}")
    assert start_rollout.status_code == 200
    assert start_rollout.json()["new_percentage"] == 10.0

    # Advance Rollout (sets percentage to 25%)
    adv1 = client.post(f"/api/v1/rollout/advance/{feature_name}")
    assert adv1.status_code == 200
    assert adv1.json()["new_percentage"] == 25.0
    assert adv1.json()["action_taken"] == "ADVANCED"

    # Step 8: Dashboard rendering
    dash_res = client.get("/dashboard")
    assert dash_res.status_code == 200
    assert "AI Feature Flag System" in dash_res.text
    assert "Version B Quality" in dash_res.text
