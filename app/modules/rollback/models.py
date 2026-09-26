from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import Base

class RollbackEventModel(Base):
    __tablename__ = "rollback_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feature_name = Column(String(100), index=True, nullable=False)
    previous_version = Column(String(100), nullable=False)
    new_version = Column(String(100), nullable=False)
    reason = Column(String(255), nullable=False)
    rollout_percentage_before = Column(Float, nullable=False)
    rollout_percentage_after = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
