from pydantic import BaseModel, Field
from typing import Optional

class FeatureFlag(BaseModel):
    feature_name: str = Field(..., description="Unique identifier for the feature flag")
    enabled: bool = Field(default=False, description="Whether the flag is active")
    rollout_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Rollout percentage (0.0 to 100.0)")
    baseline_version: str = Field(..., description="Version returned when flag disabled or fallback")
    experiment_version: str = Field(..., description="Version returned when selected for experiment")
    quality_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="Quality score threshold (0.0 to 1.0)")


class FeatureFlagUpdate(BaseModel):
    enabled: Optional[bool] = None
    rollout_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    baseline_version: Optional[str] = None
    experiment_version: Optional[str] = None
    quality_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)


class EvaluationResult(BaseModel):
    feature_name: str
    enabled: bool
    assigned_version: str
    is_experiment: bool
    reason: str
    user_id: Optional[str] = None
    bucket_score: Optional[float] = None


class UserEvaluationRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier for evaluation")
