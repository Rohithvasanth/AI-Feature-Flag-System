from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class RollbackResultResponse(BaseModel):
    feature_name: str
    executed: bool = Field(..., description="Whether rollback action was triggered")
    reason: str = Field(..., description="Details regarding rollback evaluation")
    previous_version: Optional[str] = None
    new_version: Optional[str] = None
    rollout_percentage_before: Optional[float] = None
    rollout_percentage_after: Optional[float] = None

class RollbackLogResponse(BaseModel):
    id: int
    feature_name: str
    previous_version: str
    new_version: str
    reason: str
    rollout_percentage_before: float
    rollout_percentage_after: float
    created_at: datetime
