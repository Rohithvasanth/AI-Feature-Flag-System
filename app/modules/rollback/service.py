from typing import List
from sqlalchemy.orm import Session
from app.modules.feature_flags.repository import SQLAlchemyFeatureFlagRepository
from app.modules.monitoring.service import MonitoringService
from app.modules.rollback.models import RollbackEventModel
from app.modules.rollback.schemas import (
    RollbackResultResponse,
    RollbackLogResponse
)

class RollbackService:
    def __init__(self):
        self.monitoring_service = MonitoringService()

    def evaluate_and_rollback(self, db: Session, feature_name: str) -> RollbackResultResponse:
        repo = SQLAlchemyFeatureFlagRepository(db_session=db)
        flag = repo.get(feature_name)

        if not flag:
            return RollbackResultResponse(
                feature_name=feature_name,
                executed=False,
                reason=f"Feature flag '{feature_name}' not found"
            )

        if not flag.enabled or flag.rollout_percentage == 0.0:
            return RollbackResultResponse(
                feature_name=feature_name,
                executed=False,
                reason=f"Feature flag '{feature_name}' is already disabled or set to 0.0% rollout",
                previous_version=flag.experiment_version,
                new_version=flag.baseline_version,
                rollout_percentage_before=flag.rollout_percentage,
                rollout_percentage_after=flag.rollout_percentage
            )

        # Get quality monitoring status
        status_res = self.monitoring_service.get_monitoring_status(db, feature_name)

        if status_res.alert_triggered or status_res.experiment_health.health_status == "THRESHOLD_VIOLATED":
            pct_before = flag.rollout_percentage
            pct_after = 0.0

            # Execute automatic rollback by updating flag rollout_percentage to 0.0
            flag.rollout_percentage = pct_after
            repo.update(feature_name, flag)

            reason_str = (
                f"Automatic rollback executed: experiment quality ({status_res.experiment_health.avg_quality_score:.4f}) "
                f"fell below threshold ({status_res.quality_threshold:.4f})"
            )

            # Record rollback event log
            rollback_event = RollbackEventModel(
                feature_name=feature_name,
                previous_version=flag.experiment_version,
                new_version=flag.baseline_version,
                reason=reason_str,
                rollout_percentage_before=pct_before,
                rollout_percentage_after=pct_after
            )
            db.add(rollback_event)
            db.commit()
            db.refresh(rollback_event)

            return RollbackResultResponse(
                feature_name=feature_name,
                executed=True,
                reason=reason_str,
                previous_version=flag.experiment_version,
                new_version=flag.baseline_version,
                rollout_percentage_before=pct_before,
                rollout_percentage_after=pct_after
            )

        return RollbackResultResponse(
            feature_name=feature_name,
            executed=False,
            reason=f"Quality monitoring status is {status_res.experiment_health.health_status}. Threshold ({status_res.quality_threshold:.2f}) satisfied.",
            previous_version=flag.experiment_version,
            new_version=flag.baseline_version,
            rollout_percentage_before=flag.rollout_percentage,
            rollout_percentage_after=flag.rollout_percentage
        )

    def get_rollback_history(self, db: Session, feature_name: str) -> List[RollbackLogResponse]:
        records = db.query(RollbackEventModel).filter(
            RollbackEventModel.feature_name == feature_name
        ).order_by(RollbackEventModel.created_at.desc()).all()

        return [
            RollbackLogResponse(
                id=r.id,
                feature_name=r.feature_name,
                previous_version=r.previous_version,
                new_version=r.new_version,
                reason=r.reason,
                rollout_percentage_before=r.rollout_percentage_before,
                rollout_percentage_after=r.rollout_percentage_after,
                created_at=r.created_at
            )
            for r in records
        ]
