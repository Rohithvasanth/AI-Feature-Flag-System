from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.rollback.schemas import (
    RollbackResultResponse,
    RollbackLogResponse
)
from app.modules.rollback.service import RollbackService

router = APIRouter(prefix="/api/v1/rollback", tags=["Automatic Rollback"])

def get_rollback_service() -> RollbackService:
    return RollbackService()

@router.post("/evaluate/{feature_name}", response_model=RollbackResultResponse)
def evaluate_and_rollback(
    feature_name: str,
    db: Session = Depends(get_db),
    service: RollbackService = Depends(get_rollback_service)
):
    return service.evaluate_and_rollback(db=db, feature_name=feature_name)

@router.get("/history/{feature_name}", response_model=List[RollbackLogResponse])
def get_rollback_history(
    feature_name: str,
    db: Session = Depends(get_db),
    service: RollbackService = Depends(get_rollback_service)
):
    return service.get_rollback_history(db=db, feature_name=feature_name)
