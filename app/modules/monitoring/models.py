from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import Base

class MonitoringLogModel(Base):
    __tablename__ = "monitoring_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feature_name = Column(String(100), index=True, nullable=False)
    version = Column(String(100), index=True, nullable=False)
    sample_count = Column(Integer, nullable=False, default=0)
    avg_quality_score = Column(Float, nullable=False, default=0.0)
    avg_confidence = Column(Float, nullable=False, default=0.0)
    accuracy_rate = Column(Float, nullable=False, default=0.0)
    quality_threshold = Column(Float, nullable=False, default=0.8)
    health_status = Column(String(50), nullable=False, default="HEALTHY")
    trend = Column(String(50), nullable=False, default="STABLE")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
