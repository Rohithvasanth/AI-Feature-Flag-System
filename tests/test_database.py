import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.modules.feature_flags.models import FeatureFlagModel
from app.modules.feature_flags.schemas import FeatureFlag
from app.modules.feature_flags.repository import SQLAlchemyFeatureFlagRepository

@pytest.fixture
def db_session():
    # Use SQLite in-memory engine for unit testing database persistence
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_database_table_creation_and_crud(db_session):
    repo = SQLAlchemyFeatureFlagRepository(db_session=db_session)
    
    flag = FeatureFlag(
        feature_name="postgres_test_flag",
        enabled=True,
        rollout_percentage=75.0,
        baseline_version="v1.0",
        experiment_version="v2.0",
        quality_threshold=0.85
    )
    
    # Create record
    created = repo.create(flag)
    assert created.feature_name == "postgres_test_flag"
    assert created.enabled is True
    
    # Read record from DB
    raw_model = db_session.query(FeatureFlagModel).filter_by(feature_name="postgres_test_flag").first()
    assert raw_model is not None
    assert raw_model.rollout_percentage == 75.0
    
    # Update record
    flag.rollout_percentage = 90.0
    updated = repo.update("postgres_test_flag", flag)
    assert updated.rollout_percentage == 90.0
    
    # Delete record
    assert repo.delete("postgres_test_flag") is True
    assert repo.get("postgres_test_flag") is None
