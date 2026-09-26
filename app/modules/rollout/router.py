from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.rollout.schemas import (
    RolloutStatusResponse,
    RolloutAdvanceResponse,
    RolloutLogResponse
)
from app.modules.rollout.service import RolloutService

router = APIRouter(prefix="/api/v1/rollout", tags=["Gradual Rollout"])

def get_rollout_service() -> RolloutService:
    return RolloutService()

@router.get("/status/{feature_name}", response_model=RolloutStatusResponse)
def get_rollout_status(
    feature_name: str,
    db: Session = Depends(get_db),
    service: RolloutService = Depends(get_rollout_service)
):
    return service.get_rollout_status(db=db, feature_name=feature_name)

@router.post("/start/{feature_name}", response_model=RolloutAdvanceResponse, status_code=status.HTTP_200_OK)
def start_rollout(
    feature_name: str,
    db: Session = Depends(get_db),
    service: RolloutService = Depends(get_rollout_service)
):
    return service.start_rollout(db=db, feature_name=feature_name)

@router.post("/advance/{feature_name}", response_model=RolloutAdvanceResponse, status_code=status.HTTP_200_OK)
def advance_rollout(
    feature_name: str,
    db: Session = Depends(get_db),
    service: RolloutService = Depends(get_rollout_service)
):
    return service.advance_rollout(db=db, feature_name=feature_name)

@router.get("/history/{feature_name}", response_model=List[RolloutLogResponse])
def get_rollout_history(
    feature_name: str,
    db: Session = Depends(get_db),
    service: RolloutService = Depends(get_rollout_service)
):
    return service.get_rollout_history(db=db, feature_name=feature_name)
