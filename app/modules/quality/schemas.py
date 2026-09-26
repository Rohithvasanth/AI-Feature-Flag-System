from pydantic import BaseModel, Field
from typing import Optional, Dict

class QualityRecordRequest(BaseModel):
    feature_name: str = Field(default="expense_categorizer", description="Feature flag identifier")
    version: str = Field(..., description="Model version evaluated (e.g. categorizer_v1 or categorizer_v2)")
    user_id: str = Field(..., description="User ID associated with request")
    description: str = Field(..., description="Expense description")
    predicted_category: str = Field(..., description="Category predicted by model")
    expected_category: Optional[str] = Field(None, description="Ground truth category if available")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score from model")

class QualityEvaluationRecordResponse(BaseModel):
    id: int
    feature_name: str
    version: str
    user_id: str
    description: str
    predicted_category: str
    expected_category: Optional[str] = None
    quality_score: float
    confidence: float
    is_accurate: bool

class VersionQualityStats(BaseModel):
    version: str
    total_evaluations: int
    avg_quality_score: float
    avg_confidence: float
    accuracy_rate: float

class QualityComparisonSummary(BaseModel):
    feature_name: str
    baseline_stats: VersionQualityStats
    experiment_stats: VersionQualityStats
    winner_version: str
    quality_delta: float
