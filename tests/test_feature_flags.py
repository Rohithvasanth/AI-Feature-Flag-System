import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.modules.feature_flags.schemas import FeatureFlag
from app.modules.feature_flags.repository import SQLAlchemyFeatureFlagRepository
from app.modules.feature_flags.service import FeatureFlagService

@pytest.fixture
def service():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    repo = SQLAlchemyFeatureFlagRepository(db_session=session)
    svc = FeatureFlagService(repository=repo)
    yield svc
    session.close()

def test_create_and_get_flag(service):
    flag = FeatureFlag(
        feature_name="expense_categorizer_v2",
        enabled=True,
        rollout_percentage=50.0,
        baseline_version="categorizer_v1",
        experiment_version="categorizer_v2",
        quality_threshold=0.85
    )
    created = service.create_flag(flag)
    assert created.feature_name == "expense_categorizer_v2"
    assert created.quality_threshold == 0.85

    fetched = service.get_flag("expense_categorizer_v2")
    assert fetched is not None
    assert fetched.baseline_version == "categorizer_v1"
    assert fetched.experiment_version == "categorizer_v2"

def test_evaluate_missing_flag(service):
    result = service.evaluate_flag("non_existent_flag")
    assert result.enabled is False
    assert result.assigned_version == "unknown"
    assert result.is_experiment is False
    assert result.reason == "Flag not found"

def test_evaluate_disabled_flag(service):
    flag = FeatureFlag(
        feature_name="expense_categorizer_v2",
        enabled=False,
        rollout_percentage=50.0,
        baseline_version="categorizer_v1",
        experiment_version="categorizer_v2",
        quality_threshold=0.85
    )
    service.create_flag(flag)

    result = service.evaluate_flag("expense_categorizer_v2", rollout_seed=10.0)
    assert result.enabled is False
    assert result.assigned_version == "categorizer_v1"
    assert result.is_experiment is False
    assert result.reason == "Flag is disabled"

def test_evaluate_rollout_percentage_split(service):
    flag = FeatureFlag(
        feature_name="expense_categorizer_v2",
        enabled=True,
        rollout_percentage=30.0,
        baseline_version="categorizer_v1",
        experiment_version="categorizer_v2",
        quality_threshold=0.85
    )
    service.create_flag(flag)

    # Seed 10.0 < 30.0 -> Experiment
    exp_result = service.evaluate_flag("expense_categorizer_v2", rollout_seed=10.0)
    assert exp_result.enabled is True
    assert exp_result.is_experiment is True
    assert exp_result.assigned_version == "categorizer_v2"

    # Seed 50.0 >= 30.0 -> Baseline
    base_result = service.evaluate_flag("expense_categorizer_v2", rollout_seed=50.0)
    assert base_result.enabled is True
    assert base_result.is_experiment is False
    assert base_result.assigned_version == "categorizer_v1"

def test_evaluate_boundary_rollout_percentages(service):
    # 100% Rollout
    flag_100 = FeatureFlag(
        feature_name="flag_100",
        enabled=True,
        rollout_percentage=100.0,
        baseline_version="base",
        experiment_version="exp",
        quality_threshold=0.9
    )
    service.create_flag(flag_100)
    res_100 = service.evaluate_flag("flag_100", rollout_seed=99.9)
    assert res_100.assigned_version == "exp"

    # 0% Rollout
    flag_0 = FeatureFlag(
        feature_name="flag_0",
        enabled=True,
        rollout_percentage=0.0,
        baseline_version="base",
        experiment_version="exp",
        quality_threshold=0.9
    )
    service.create_flag(flag_0)
    res_0 = service.evaluate_flag("flag_0", rollout_seed=0.0)
    assert res_0.assigned_version == "base"

def test_update_and_delete_flag(service):
    flag = FeatureFlag(
        feature_name="test_flag",
        enabled=True,
        rollout_percentage=10.0,
        baseline_version="v1",
        experiment_version="v2",
        quality_threshold=0.7
    )
    service.create_flag(flag)

    flag.rollout_percentage = 90.0
    updated = service.update_flag("test_flag", flag)
    assert updated.rollout_percentage == 90.0

    assert service.delete_flag("test_flag") is True
    assert service.get_flag("test_flag") is None
