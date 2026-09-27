from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.shadow.schemas import (
    ShadowStatusResponse,
    ShadowLogResponse
)
from app.modules.shadow.service import ShadowService

router = APIRouter(prefix="/api/v1/shadow", tags=["Shadow Mode"])

def get_shadow_service() -> ShadowService:
    return ShadowService()

@router.post("/enable/{feature_name}", response_model=ShadowStatusResponse)
def enable_shadow_mode(
    feature_name: str,
    shadow_version: str = "categorizer_v2",
    db: Session = Depends(get_db),
    service: ShadowService = Depends(get_shadow_service)
):
    service.enable_shadow_mode(db=db, feature_name=feature_name, shadow_version=shadow_version)
    return service.get_shadow_status(db=db, feature_name=feature_name)

@router.post("/disable/{feature_name}", response_model=ShadowStatusResponse)
def disable_shadow_mode(
    feature_name: str,
    db: Session = Depends(get_db),
    service: ShadowService = Depends(get_shadow_service)
):
    service.disable_shadow_mode(db=db, feature_name=feature_name)
    return service.get_shadow_status(db=db, feature_name=feature_name)

@router.get("/status/{feature_name}", response_model=ShadowStatusResponse)
def get_shadow_status(
    feature_name: str,
    db: Session = Depends(get_db),
    service: ShadowService = Depends(get_shadow_service)
):
    return service.get_shadow_status(db=db, feature_name=feature_name)

@router.get("/history/{feature_name}", response_model=List[ShadowLogResponse])
def get_shadow_history(
    feature_name: str,
    db: Session = Depends(get_db),
    service: ShadowService = Depends(get_shadow_service)
):
    return service.get_shadow_history(db=db, feature_name=feature_name)
