from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.feature_flags.schemas import (
    FeatureFlag,
    FeatureFlagUpdate,
    EvaluationResult,
    UserEvaluationRequest
)
from app.modules.feature_flags.repository import SQLAlchemyFeatureFlagRepository
from app.modules.feature_flags.service import FeatureFlagService

router = APIRouter(prefix="/api/v1/flags", tags=["Feature Flags"])

def get_service(db: Session = Depends(get_db)) -> FeatureFlagService:
    repo = SQLAlchemyFeatureFlagRepository(db_session=db)
    return FeatureFlagService(repository=repo)

@router.post("/", response_model=FeatureFlag, status_code=status.HTTP_201_CREATED)
def create_feature_flag(
    flag: FeatureFlag,
    service: FeatureFlagService = Depends(get_service)
):
    existing = service.get_flag(flag.feature_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Feature flag '{flag.feature_name}' already exists"
        )
    return service.create_flag(flag)

@router.get("/", response_model=List[FeatureFlag])
def list_feature_flags(service: FeatureFlagService = Depends(get_service)):
    return service.list_flags()

@router.get("/{feature_name}", response_model=FeatureFlag)
def get_feature_flag(
    feature_name: str,
    service: FeatureFlagService = Depends(get_service)
):
    flag = service.get_flag(feature_name)
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{feature_name}' not found"
        )
    return flag

@router.put("/{feature_name}", response_model=FeatureFlag)
def update_feature_flag(
    feature_name: str,
    updates: FeatureFlagUpdate,
    service: FeatureFlagService = Depends(get_service)
):
    existing = service.get_flag(feature_name)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{feature_name}' not found"
        )

    # Merge updates into existing flag model
    update_data = updates.model_dump(exclude_unset=True)
    merged_flag_data = existing.model_dump()
    merged_flag_data.update(update_data)
    updated_flag = FeatureFlag(**merged_flag_data)

    return service.update_flag(feature_name, updated_flag)

@router.delete("/{feature_name}", status_code=status.HTTP_200_OK)
def delete_feature_flag(
    feature_name: str,
    service: FeatureFlagService = Depends(get_service)
):
    deleted = service.delete_flag(feature_name)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{feature_name}' not found"
        )
    return {"message": f"Feature flag '{feature_name}' deleted successfully"}

@router.post("/{feature_name}/evaluate", response_model=EvaluationResult)
def evaluate_feature_flag_for_user(
    feature_name: str,
    request: UserEvaluationRequest,
    service: FeatureFlagService = Depends(get_service)
):
    flag = service.get_flag(feature_name)
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{feature_name}' not found"
        )
    return service.evaluate_flag_for_user(feature_name=feature_name, user_id=request.user_id)
