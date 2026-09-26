from typing import List, Optional
from sqlalchemy.orm import Session
from app.modules.feature_flags.schemas import FeatureFlag
from app.modules.feature_flags.models import FeatureFlagModel

class SQLAlchemyFeatureFlagRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def _to_schema(self, model: FeatureFlagModel) -> FeatureFlag:
        return FeatureFlag(
            feature_name=model.feature_name,
            enabled=model.enabled,
            rollout_percentage=model.rollout_percentage,
            baseline_version=model.baseline_version,
            experiment_version=model.experiment_version,
            quality_threshold=model.quality_threshold
        )

    def create(self, flag: FeatureFlag) -> FeatureFlag:
        db_flag = FeatureFlagModel(
            feature_name=flag.feature_name,
            enabled=flag.enabled,
            rollout_percentage=flag.rollout_percentage,
            baseline_version=flag.baseline_version,
            experiment_version=flag.experiment_version,
            quality_threshold=flag.quality_threshold
        )
        self.db.add(db_flag)
        self.db.commit()
        self.db.refresh(db_flag)
        return self._to_schema(db_flag)

    def get(self, feature_name: str) -> Optional[FeatureFlag]:
        db_flag = self.db.query(FeatureFlagModel).filter(FeatureFlagModel.feature_name == feature_name).first()
        if db_flag:
            return self._to_schema(db_flag)
        return None

    def list_all(self) -> List[FeatureFlag]:
        db_flags = self.db.query(FeatureFlagModel).all()
        return [self._to_schema(f) for f in db_flags]

    def update(self, feature_name: str, updated_flag: FeatureFlag) -> Optional[FeatureFlag]:
        db_flag = self.db.query(FeatureFlagModel).filter(FeatureFlagModel.feature_name == feature_name).first()
        if not db_flag:
            return None
        
        db_flag.enabled = updated_flag.enabled
        db_flag.rollout_percentage = updated_flag.rollout_percentage
        db_flag.baseline_version = updated_flag.baseline_version
        db_flag.experiment_version = updated_flag.experiment_version
        db_flag.quality_threshold = updated_flag.quality_threshold
        
        self.db.commit()
        self.db.refresh(db_flag)
        return self._to_schema(db_flag)

    def delete(self, feature_name: str) -> bool:
        db_flag = self.db.query(FeatureFlagModel).filter(FeatureFlagModel.feature_name == feature_name).first()
        if not db_flag:
            return False
        
        self.db.delete(db_flag)
        self.db.commit()
        return True

    def clear(self):
        self.db.query(FeatureFlagModel).delete()
        self.db.commit()

# Alias for backwards compatibility if needed
PostgresFeatureFlagRepository = SQLAlchemyFeatureFlagRepository
