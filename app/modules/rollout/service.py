from typing import List, Optional
from sqlalchemy.orm import Session
from app.modules.feature_flags.repository import SQLAlchemyFeatureFlagRepository
from app.modules.monitoring.service import MonitoringService
from app.modules.rollback.service import RollbackService
from app.modules.rollout.models import RolloutLogModel
from app.modules.rollout.schemas import (
    RolloutStatusResponse,
    RolloutAdvanceResponse,
    RolloutLogResponse
)

ROLLOUT_STAGES = [0.0, 10.0, 25.0, 50.0, 75.0, 100.0]

class RolloutService:
    def __init__(self):
        self.monitoring_service = MonitoringService()
        self.rollback_service = RollbackService()

    def _get_current_stage_index(self, percentage: float) -> int:
        for idx, stage_pct in enumerate(ROLLOUT_STAGES):
            if percentage <= stage_pct:
                return idx
        return len(ROLLOUT_STAGES) - 1

    def get_rollout_status(self, db: Session, feature_name: str) -> RolloutStatusResponse:
        repo = SQLAlchemyFeatureFlagRepository(db_session=db)
        flag = repo.get(feature_name)

        if not flag:
            return RolloutStatusResponse(
                feature_name=feature_name,
                enabled=False,
                current_percentage=0.0,
                current_stage_index=0,
                next_target_percentage=10.0,
                quality_threshold=0.80,
                is_healthy=False,
                is_completed=False
            )

        curr_pct = flag.rollout_percentage
        idx = self._get_current_stage_index(curr_pct)
        next_pct = ROLLOUT_STAGES[idx + 1] if idx + 1 < len(ROLLOUT_STAGES) else None
        
        status_res = self.monitoring_service.get_monitoring_status(db, feature_name)

        return RolloutStatusResponse(
            feature_name=feature_name,
            enabled=flag.enabled,
            current_percentage=curr_pct,
            current_stage_index=idx,
            next_target_percentage=next_pct,
            quality_threshold=flag.quality_threshold,
            is_healthy=status_res.is_healthy,
            is_completed=(curr_pct >= 100.0)
        )

    def start_rollout(self, db: Session, feature_name: str) -> RolloutAdvanceResponse:
        repo = SQLAlchemyFeatureFlagRepository(db_session=db)
        flag = repo.get(feature_name)

        if not flag:
            return RolloutAdvanceResponse(
                feature_name=feature_name,
                action_taken="BLOCKED",
                previous_percentage=0.0,
                new_percentage=0.0,
                reason=f"Feature flag '{feature_name}' not found"
            )

        from_pct = flag.rollout_percentage
        to_pct = 10.0  # Initial rollout stage

        flag.enabled = True
        flag.rollout_percentage = to_pct
        repo.update(feature_name, flag)

        log_entry = RolloutLogModel(
            feature_name=feature_name,
            from_percentage=from_pct,
            to_percentage=to_pct,
            status="STARTED",
            reason=f"Gradual rollout started at {to_pct:.1f}%"
        )
        db.add(log_entry)
        db.commit()

        return RolloutAdvanceResponse(
            feature_name=feature_name,
            action_taken="STARTED",
            previous_percentage=from_pct,
            new_percentage=to_pct,
            reason=f"Gradual rollout initialized to {to_pct:.1f}%"
        )

    def advance_rollout(self, db: Session, feature_name: str) -> RolloutAdvanceResponse:
        repo = SQLAlchemyFeatureFlagRepository(db_session=db)
        flag = repo.get(feature_name)

        if not flag:
            return RolloutAdvanceResponse(
                feature_name=feature_name,
                action_taken="BLOCKED",
                previous_percentage=0.0,
                new_percentage=0.0,
                reason=f"Feature flag '{feature_name}' not found"
            )

        if flag.rollout_percentage >= 100.0:
            return RolloutAdvanceResponse(
                feature_name=feature_name,
                action_taken="COMPLETED",
                previous_percentage=100.0,
                new_percentage=100.0,
                reason="Rollout has already reached 100%"
            )

        # Quality Gating Check via Monitoring Service
        status_res = self.monitoring_service.get_monitoring_status(db, feature_name)

        if status_res.alert_triggered or status_res.experiment_health.health_status == "THRESHOLD_VIOLATED":
            # Quality threshold violated! Trigger automatic rollback to 0%
            rb_res = self.rollback_service.evaluate_and_rollback(db, feature_name)
            
            log_entry = RolloutLogModel(
                feature_name=feature_name,
                from_percentage=flag.rollout_percentage,
                to_percentage=0.0,
                status="ROLLED_BACK",
                reason=f"Advancement blocked by threshold violation: {rb_res.reason}"
            )
            db.add(log_entry)
            db.commit()

            return RolloutAdvanceResponse(
                feature_name=feature_name,
                action_taken="ROLLED_BACK",
                previous_percentage=flag.rollout_percentage,
                new_percentage=0.0,
                reason=f"Quality threshold violated ({status_res.experiment_health.avg_quality_score:.4f} < {status_res.quality_threshold:.4f}). Rollback executed to 0.0%."
            )

        # Quality is healthy -> Advance to next stage in ROLLOUT_STAGES
        idx = self._get_current_stage_index(flag.rollout_percentage)
        next_stage_pct = ROLLOUT_STAGES[idx + 1] if idx + 1 < len(ROLLOUT_STAGES) else 100.0

        from_pct = flag.rollout_percentage
        flag.rollout_percentage = next_stage_pct
        repo.update(feature_name, flag)

        action_name = "COMPLETED" if next_stage_pct == 100.0 else "ADVANCED"

        log_entry = RolloutLogModel(
            feature_name=feature_name,
            from_percentage=from_pct,
            to_percentage=next_stage_pct,
            status=action_name,
            reason=f"Quality score satisfies threshold ({status_res.quality_threshold:.2f}). Rollout advanced from {from_pct:.1f}% to {next_stage_pct:.1f}%."
        )
        db.add(log_entry)
        db.commit()

        return RolloutAdvanceResponse(
            feature_name=feature_name,
            action_taken=action_name,
            previous_percentage=from_pct,
            new_percentage=next_stage_pct,
            reason=f"Quality threshold satisfied. Traffic rollout advanced from {from_pct:.1f}% to {next_stage_pct:.1f}%."
        )

    def get_rollout_history(self, db: Session, feature_name: str) -> List[RolloutLogResponse]:
        records = db.query(RolloutLogModel).filter(
            RolloutLogModel.feature_name == feature_name
        ).order_by(RolloutLogModel.created_at.desc()).all()

        return [
            RolloutLogResponse(
                id=r.id,
                feature_name=r.feature_name,
                from_percentage=r.from_percentage,
                to_percentage=r.to_percentage,
                status=r.status,
                reason=r.reason,
                created_at=r.created_at
            )
            for r in records
        ]
