from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import Base

class RolloutLogModel(Base):
    __tablename__ = "rollout_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feature_name = Column(String(100), index=True, nullable=False)
    from_percentage = Column(Float, nullable=False)
    to_percentage = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)  # STARTED, ADVANCED, ROLLED_BACK, COMPLETED
    reason = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
