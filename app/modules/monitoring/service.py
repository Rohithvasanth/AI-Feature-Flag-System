from typing import List, Optional
from sqlalchemy.orm import Session
from app.modules.feature_flags.repository import SQLAlchemyFeatureFlagRepository
from app.modules.quality.models import QualityEvaluationModel
from app.modules.monitoring.models import MonitoringLogModel
from app.modules.monitoring.schemas import (
    VersionMonitoringHealth,
    MonitoringStatusResponse,
    MonitoringLogResponse
)

class MonitoringService:
    def get_version_health(
        self,
        db: Session,
        feature_name: str,
        version: str,
        threshold: float
    ) -> VersionMonitoringHealth:
        evals = db.query(QualityEvaluationModel).filter(
            QualityEvaluationModel.feature_name == feature_name,
            QualityEvaluationModel.version == version
        ).order_by(QualityEvaluationModel.created_at.asc()).all()

        total = len(evals)
        if total == 0:
            return VersionMonitoringHealth(
                version=version,
                sample_count=0,
                avg_quality_score=0.0,
                avg_confidence=0.0,
                accuracy_rate=0.0,
                health_status="INSUFFICIENT_DATA",
                trend="STABLE"
            )

        avg_quality = sum(e.quality_score for e in evals) / total
        avg_conf = sum(e.confidence for e in evals) / total
        accurate_count = sum(1 for e in evals if e.is_accurate)
        accuracy_rate = (accurate_count / total) * 100.0

        # Health status check against threshold
        if avg_quality >= threshold:
            health_status = "HEALTHY"
        else:
            health_status = "THRESHOLD_VIOLATED"

        # Trend detection (comparing last 5 vs earlier)
        if total >= 4:
            half = total // 2
            earlier_avg = sum(e.quality_score for e in evals[:half]) / half
            recent_avg = sum(e.quality_score for e in evals[half:]) / (total - half)
            
            if recent_avg > earlier_avg + 0.05:
                trend = "IMPROVING"
            elif recent_avg < earlier_avg - 0.05:
                trend = "DEGRADING"
            else:
                trend = "STABLE"
        else:
            trend = "STABLE"

        return VersionMonitoringHealth(
            version=version,
            sample_count=total,
            avg_quality_score=round(avg_quality, 4),
            avg_confidence=round(avg_conf, 4),
            accuracy_rate=round(accuracy_rate, 2),
            health_status=health_status,
            trend=trend
        )

    def get_monitoring_status(
        self, db: Session, feature_name: str
    ) -> MonitoringStatusResponse:
        repo = SQLAlchemyFeatureFlagRepository(db_session=db)
        flag = repo.get(feature_name)

        threshold = flag.quality_threshold if flag else 0.80
        baseline_v = flag.baseline_version if flag else "categorizer_v1"
        experiment_v = flag.experiment_version if flag else "categorizer_v2"

        base_health = self.get_version_health(db, feature_name, baseline_v, threshold)
        exp_health = self.get_version_health(db, feature_name, experiment_v, threshold)

        alert_triggered = (exp_health.health_status == "THRESHOLD_VIOLATED")
        is_healthy = not alert_triggered

        return MonitoringStatusResponse(
            feature_name=feature_name,
            quality_threshold=threshold,
            is_healthy=is_healthy,
            alert_triggered=alert_triggered,
            baseline_health=base_health,
            experiment_health=exp_health
        )

    def take_snapshot(
        self, db: Session, feature_name: str
    ) -> List[MonitoringLogResponse]:
        status_res = self.get_monitoring_status(db, feature_name)
        logs = []

        for health in [status_res.baseline_health, status_res.experiment_health]:
            if health.sample_count > 0:
                log_entry = MonitoringLogModel(
                    feature_name=feature_name,
                    version=health.version,
                    sample_count=health.sample_count,
                    avg_quality_score=health.avg_quality_score,
                    avg_confidence=health.avg_confidence,
                    accuracy_rate=health.accuracy_rate,
                    quality_threshold=status_res.quality_threshold,
                    health_status=health.health_status,
                    trend=health.trend
                )
                db.add(log_entry)
                db.commit()
                db.refresh(log_entry)
                logs.append(MonitoringLogResponse(
                    id=log_entry.id,
                    feature_name=log_entry.feature_name,
                    version=log_entry.version,
                    sample_count=log_entry.sample_count,
                    avg_quality_score=log_entry.avg_quality_score,
                    avg_confidence=log_entry.avg_confidence,
                    accuracy_rate=log_entry.accuracy_rate,
                    quality_threshold=log_entry.quality_threshold,
                    health_status=log_entry.health_status,
                    trend=log_entry.trend,
                    created_at=log_entry.created_at
                ))
        return logs

    def get_monitoring_history(
        self, db: Session, feature_name: str
    ) -> List[MonitoringLogResponse]:
        records = db.query(MonitoringLogModel).filter(
            MonitoringLogModel.feature_name == feature_name
        ).order_by(MonitoringLogModel.created_at.desc()).all()

        return [
            MonitoringLogResponse(
                id=r.id,
                feature_name=r.feature_name,
                version=r.version,
                sample_count=r.sample_count,
                avg_quality_score=r.avg_quality_score,
                avg_confidence=r.avg_confidence,
                accuracy_rate=r.accuracy_rate,
                quality_threshold=r.quality_threshold,
                health_status=r.health_status,
                trend=r.trend,
                created_at=r.created_at
            )
            for r in records
        ]
