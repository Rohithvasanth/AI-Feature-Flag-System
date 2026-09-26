from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.quality.schemas import (
    QualityRecordRequest,
    QualityEvaluationRecordResponse,
    QualityComparisonSummary
)
from app.modules.quality.service import QualityEvaluationService

router = APIRouter(prefix="/api/v1/quality", tags=["Quality Evaluation"])

def get_quality_service() -> QualityEvaluationService:
    return QualityEvaluationService()

@router.post("/evaluate", response_model=QualityEvaluationRecordResponse, status_code=status.HTTP_201_CREATED)
def record_quality_evaluation(
    request: QualityRecordRequest,
    db: Session = Depends(get_db),
    service: QualityEvaluationService = Depends(get_quality_service)
):
    return service.record_evaluation(db=db, req=request)

@router.get("/summary/{feature_name}", response_model=QualityComparisonSummary)
def get_quality_summary(
    feature_name: str,
    baseline_version: str = Query("categorizer_v1", description="Baseline model version"),
    experiment_version: str = Query("categorizer_v2", description="Experiment model version"),
    db: Session = Depends(get_db),
    service: QualityEvaluationService = Depends(get_quality_service)
):
    return service.compare_versions(
        db=db,
        feature_name=feature_name,
        baseline_version=baseline_version,
        experiment_version=experiment_version
    )
