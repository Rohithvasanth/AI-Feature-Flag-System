from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Float, DateTime
from app.core.database import Base

class FeatureFlagModel(Base):
    __tablename__ = "feature_flags"

    feature_name = Column(String(100), primary_key=True, index=True)
    enabled = Column(Boolean, default=False, nullable=False)
    rollout_percentage = Column(Float, default=0.0, nullable=False)
    baseline_version = Column(String(100), nullable=False)
    experiment_version = Column(String(100), nullable=False)
    quality_threshold = Column(Float, default=0.8, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
