from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

class RolloutStatusResponse(BaseModel):
    feature_name: str
    enabled: bool
    current_percentage: float
    current_stage_index: int
    next_target_percentage: Optional[float]
    quality_threshold: float
    is_healthy: bool
    is_completed: bool

class RolloutAdvanceResponse(BaseModel):
    feature_name: str
    action_taken: str  # ADVANCED, ROLLED_BACK, BLOCKED, COMPLETED
    previous_percentage: float
    new_percentage: float
    reason: str

class RolloutLogResponse(BaseModel):
    id: int
    feature_name: str
    from_percentage: float
    to_percentage: float
    status: str
    reason: str
    created_at: datetime
