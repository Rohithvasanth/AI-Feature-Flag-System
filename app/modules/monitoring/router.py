from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.monitoring.schemas import (
    MonitoringStatusResponse,
    MonitoringLogResponse
)
from app.modules.monitoring.service import MonitoringService

router = APIRouter(prefix="/api/v1/monitoring", tags=["Quality Monitoring"])

def get_monitoring_service() -> MonitoringService:
    return MonitoringService()

@router.get("/status/{feature_name}", response_model=MonitoringStatusResponse)
def get_monitoring_status(
    feature_name: str,
    db: Session = Depends(get_db),
    service: MonitoringService = Depends(get_monitoring_service)
):
    return service.get_monitoring_status(db=db, feature_name=feature_name)

@router.post("/snapshot/{feature_name}", response_model=List[MonitoringLogResponse], status_code=status.HTTP_201_CREATED)
def record_monitoring_snapshot(
    feature_name: str,
    db: Session = Depends(get_db),
    service: MonitoringService = Depends(get_monitoring_service)
):
    return service.take_snapshot(db=db, feature_name=feature_name)

@router.get("/history/{feature_name}", response_model=List[MonitoringLogResponse])
def get_monitoring_history(
    feature_name: str,
    db: Session = Depends(get_db),
    service: MonitoringService = Depends(get_monitoring_service)
):
    return service.get_monitoring_history(db=db, feature_name=feature_name)
