import random
from typing import Optional, List, Union
from app.modules.feature_flags.schemas import FeatureFlag, EvaluationResult
from app.modules.feature_flags.repository import SQLAlchemyFeatureFlagRepository
from app.modules.feature_flags.hashing import compute_user_bucket

class FeatureFlagService:
    def __init__(self, repository: SQLAlchemyFeatureFlagRepository):
        self.repository = repository

    def create_flag(self, flag: FeatureFlag) -> FeatureFlag:
        return self.repository.create(flag)

    def get_flag(self, feature_name: str) -> Optional[FeatureFlag]:
        return self.repository.get(feature_name)

    def list_flags(self) -> List[FeatureFlag]:
        return self.repository.list_all()

    def update_flag(self, feature_name: str, flag: FeatureFlag) -> Optional[FeatureFlag]:
        return self.repository.update(feature_name, flag)

    def delete_flag(self, feature_name: str) -> bool:
        return self.repository.delete(feature_name)

    def evaluate_flag(
        self,
        feature_name: str,
        rollout_seed: Optional[float] = None,
        user_id: Optional[str] = None
    ) -> EvaluationResult:
        """
        Evaluates a feature flag for target assignment.

        :param feature_name: Unique feature flag identifier
        :param rollout_seed: Seed float between 0.0 and 100.0
        :param user_id: Optional user identifier for metadata tracking
        :return: EvaluationResult containing assigned version and metadata
        """
        flag = self.repository.get(feature_name)

        if not flag:
            return EvaluationResult(
                feature_name=feature_name,
                enabled=False,
                assigned_version="unknown",
                is_experiment=False,
                reason="Flag not found",
                user_id=user_id,
                bucket_score=rollout_seed
            )

        if not flag.enabled:
            return EvaluationResult(
                feature_name=feature_name,
                enabled=False,
                assigned_version=flag.baseline_version,
                is_experiment=False,
                reason="Flag is disabled",
                user_id=user_id,
                bucket_score=rollout_seed
            )

        # Flag is enabled, compute rollout version based on rollout_seed
        if rollout_seed is None:
            rollout_seed = random.uniform(0.0, 100.0)

        is_experiment = rollout_seed < flag.rollout_percentage
        assigned_version = flag.experiment_version if is_experiment else flag.baseline_version

        reason = (
            f"Assigned experiment version ({rollout_seed:.2f} < {flag.rollout_percentage:.2f}%)"
            if is_experiment
            else f"Assigned baseline version ({rollout_seed:.2f} >= {flag.rollout_percentage:.2f}%)"
        )

        return EvaluationResult(
            feature_name=feature_name,
            enabled=True,
            assigned_version=assigned_version,
            is_experiment=is_experiment,
            reason=reason,
            user_id=user_id,
            bucket_score=round(rollout_seed, 4)
        )

    def evaluate_flag_for_user(self, feature_name: str, user_id: str) -> EvaluationResult:
        """
        Evaluates a feature flag deterministically for a specific user using user_id + feature_name hashing.

        :param feature_name: Unique feature flag identifier
        :param user_id: Unique user identifier
        :return: EvaluationResult with consistent user assignment
        """
        bucket_score = compute_user_bucket(user_id=user_id, feature_name=feature_name)
        return self.evaluate_flag(
            feature_name=feature_name,
            rollout_seed=bucket_score,
            user_id=user_id
        )
