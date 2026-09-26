import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.modules.feature_flags.schemas import FeatureFlag
from app.modules.feature_flags.repository import SQLAlchemyFeatureFlagRepository
from app.modules.feature_flags.service import FeatureFlagService
from app.modules.feature_flags.hashing import compute_user_bucket

@pytest.fixture
def service():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    repo = SQLAlchemyFeatureFlagRepository(db_session=session)
    svc = FeatureFlagService(repository=repo)
    
    flag = FeatureFlag(
        feature_name="ai_categorizer_v2",
        enabled=True,
        rollout_percentage=50.0,
        baseline_version="version_a",
        experiment_version="version_b",
        quality_threshold=0.8
    )
    svc.create_flag(flag)
    yield svc
    session.close()

def test_hashing_consistency():
    user_id = "user_12345"
    feature_name = "ai_categorizer_v2"
    
    bucket1 = compute_user_bucket(user_id, feature_name)
    bucket2 = compute_user_bucket(user_id, feature_name)
    
    assert bucket1 == bucket2
    assert 0.0 <= bucket1 < 100.0

def test_user_assignment_repeatability(service):
    user_id = "user_999"
    feature_name = "ai_categorizer_v2"
    
    # Repeat evaluation 50 times
    results = [service.evaluate_flag_for_user(feature_name, user_id) for _ in range(50)]
    
    first_assigned = results[0].assigned_version
    first_bucket = results[0].bucket_score
    
    for r in results:
        assert r.assigned_version == first_assigned
        assert r.bucket_score == first_bucket
        assert r.user_id == user_id

def test_different_users_get_independent_assignments(service):
    res_user1 = service.evaluate_flag_for_user("ai_categorizer_v2", "user_1")
    res_user2 = service.evaluate_flag_for_user("ai_categorizer_v2", "user_2")
    
    assert res_user1.bucket_score != res_user2.bucket_score

def test_different_features_same_user(service):
    flag2 = FeatureFlag(
        feature_name="another_feature",
        enabled=True,
        rollout_percentage=50.0,
        baseline_version="v1",
        experiment_version="v2",
        quality_threshold=0.8
    )
    service.create_flag(flag2)
    
    res1 = service.evaluate_flag_for_user("ai_categorizer_v2", "user_same")
    res2 = service.evaluate_flag_for_user("another_feature", "user_same")
    
    assert res1.bucket_score != res2.bucket_score

def test_disabled_flag_for_user(service):
    disabled_flag = FeatureFlag(
        feature_name="disabled_feature",
        enabled=False,
        rollout_percentage=99.0,
        baseline_version="base_v1",
        experiment_version="exp_v2",
        quality_threshold=0.8
    )
    service.create_flag(disabled_flag)
    
    res = service.evaluate_flag_for_user("disabled_feature", "user_test")
    assert res.enabled is False
    assert res.assigned_version == "base_v1"
    assert res.is_experiment is False

def test_rollout_distribution(service):
    # Evaluate 1000 users against a 50% rollout flag
    experiment_count = 0
    total_users = 1000
    
    for i in range(total_users):
        user_id = f"test_user_{i}"
        res = service.evaluate_flag_for_user("ai_categorizer_v2", user_id)
        if res.is_experiment:
            experiment_count += 1
            
    # Check that distribution is balanced roughly ~50% (e.g. between 44% and 56%)
    percentage = (experiment_count / total_users) * 100.0
    assert 44.0 <= percentage <= 56.0
