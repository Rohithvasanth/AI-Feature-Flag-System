from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

class VersionMonitoringHealth(BaseModel):
    version: str
    sample_count: int
    avg_quality_score: float
    avg_confidence: float
    accuracy_rate: float
    health_status: str  # "HEALTHY", "THRESHOLD_VIOLATED", "INSUFFICIENT_DATA"
    trend: str          # "STABLE", "IMPROVING", "DEGRADING"

class MonitoringStatusResponse(BaseModel):
    feature_name: str
    quality_threshold: float
    is_healthy: bool
    alert_triggered: bool
    baseline_health: VersionMonitoringHealth
    experiment_health: VersionMonitoringHealth

class MonitoringLogResponse(BaseModel):
    id: int
    feature_name: str
    version: str
    sample_count: int
    avg_quality_score: float
    avg_confidence: float
    accuracy_rate: float
    quality_threshold: float
    health_status: str
    trend: str
    created_at: datetime
