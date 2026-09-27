from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class ShadowStatusResponse(BaseModel):
    feature_name: str
    shadow_enabled: bool
    shadow_version: str
    total_shadow_evaluations: int
    category_match_rate: float
    avg_prod_latency_ms: float
    avg_shadow_latency_ms: float

class ShadowLogResponse(BaseModel):
    id: int
    feature_name: str
    user_id: str
    description: str
    amount: float
    prod_version: str
    prod_category: str
    prod_latency_ms: float
    shadow_version: str
    shadow_category: str
    shadow_latency_ms: float
    category_matched: bool
    created_at: datetime
