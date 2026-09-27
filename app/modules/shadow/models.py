from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from app.core.database import Base

class ShadowLogModel(Base):
    __tablename__ = "shadow_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feature_name = Column(String(100), index=True, nullable=False)
    user_id = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    prod_version = Column(String(100), nullable=False)
    prod_category = Column(String(100), nullable=False)
    prod_latency_ms = Column(Float, nullable=False, default=0.0)
    shadow_version = Column(String(100), nullable=False)
    shadow_category = Column(String(100), nullable=False)
    shadow_latency_ms = Column(Float, nullable=False, default=0.0)
    category_matched = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class ShadowConfigModel(Base):
    __tablename__ = "shadow_configs"

    feature_name = Column(String(100), primary_key=True, index=True)
    shadow_enabled = Column(Boolean, default=False, nullable=False)
    shadow_version = Column(String(100), default="categorizer_v2", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
