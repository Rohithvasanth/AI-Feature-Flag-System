from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from app.core.database import Base

class QualityEvaluationModel(Base):
    __tablename__ = "quality_evaluations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feature_name = Column(String(100), index=True, nullable=False)
    version = Column(String(100), index=True, nullable=False)
    user_id = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    predicted_category = Column(String(100), nullable=False)
    expected_category = Column(String(100), nullable=True)
    quality_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    is_accurate = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
