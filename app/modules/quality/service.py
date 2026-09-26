from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.modules.quality.models import QualityEvaluationModel
from app.modules.quality.schemas import (
    QualityRecordRequest,
    QualityEvaluationRecordResponse,
    VersionQualityStats,
    QualityComparisonSummary
)

class QualityEvaluationService:
    @staticmethod
    def calculate_quality_score(confidence: float, is_accurate: bool) -> float:
        """
        Calculates a normalized quality score between 0.0 and 1.0.
        :param confidence: Model confidence score (0.0 to 1.0)
        :param is_accurate: Ground truth accuracy match
        :return: Quality score float
        """
        if is_accurate:
            score = 0.60 + (0.40 * confidence)
        else:
            score = 0.20 * confidence
        return round(min(max(score, 0.0), 1.0), 4)

    def record_evaluation(
        self, db: Session, req: QualityRecordRequest
    ) -> QualityEvaluationRecordResponse:
        # Determine ground truth accuracy match if expected category is supplied
        if req.expected_category:
            is_accurate = req.predicted_category.strip().lower() == req.expected_category.strip().lower()
        else:
            is_accurate = True  # Default assume accurate when ground truth absent

        quality_score = self.calculate_quality_score(
            confidence=req.confidence,
            is_accurate=is_accurate
        )

        db_model = QualityEvaluationModel(
            feature_name=req.feature_name,
            version=req.version,
            user_id=req.user_id,
            description=req.description,
            predicted_category=req.predicted_category,
            expected_category=req.expected_category,
            quality_score=quality_score,
            confidence=req.confidence,
            is_accurate=is_accurate
        )
        db.add(db_model)
        db.commit()
        db.refresh(db_model)

        return QualityEvaluationRecordResponse(
            id=db_model.id,
            feature_name=db_model.feature_name,
            version=db_model.version,
            user_id=db_model.user_id,
            description=db_model.description,
            predicted_category=db_model.predicted_category,
            expected_category=db_model.expected_category,
            quality_score=db_model.quality_score,
            confidence=db_model.confidence,
            is_accurate=db_model.is_accurate
        )

    def get_version_stats(self, db: Session, feature_name: str, version: str) -> VersionQualityStats:
        evals = db.query(QualityEvaluationModel).filter(
            QualityEvaluationModel.feature_name == feature_name,
            QualityEvaluationModel.version == version
        ).all()

        if not evals:
            return VersionQualityStats(
                version=version,
                total_evaluations=0,
                avg_quality_score=0.0,
                avg_confidence=0.0,
                accuracy_rate=0.0
            )

        total = len(evals)
        avg_quality = sum(e.quality_score for e in evals) / total
        avg_conf = sum(e.confidence for e in evals) / total
        accurate_count = sum(1 for e in evals if e.is_accurate)
        accuracy_rate = (accurate_count / total) * 100.0

        return VersionQualityStats(
            version=version,
            total_evaluations=total,
            avg_quality_score=round(avg_quality, 4),
            avg_confidence=round(avg_conf, 4),
            accuracy_rate=round(accuracy_rate, 2)
        )

    def compare_versions(
        self,
        db: Session,
        feature_name: str,
        baseline_version: str = "categorizer_v1",
        experiment_version: str = "categorizer_v2"
    ) -> QualityComparisonSummary:
        base_stats = self.get_version_stats(db, feature_name, baseline_version)
        exp_stats = self.get_version_stats(db, feature_name, experiment_version)

        delta = exp_stats.avg_quality_score - base_stats.avg_quality_score

        if exp_stats.avg_quality_score >= base_stats.avg_quality_score:
            winner = experiment_version
        else:
            winner = baseline_version

        return QualityComparisonSummary(
            feature_name=feature_name,
            baseline_stats=base_stats,
            experiment_stats=exp_stats,
            winner_version=winner,
            quality_delta=round(delta, 4)
        )
