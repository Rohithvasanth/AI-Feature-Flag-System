import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def get_engine(db_url: str = None):
    url = db_url or settings.DATABASE_URL
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            pass
        return engine
    except Exception as e:
        logger.warning(f"Failed to connect to primary database ({url}): {e}. Falling back to SQLite memory database.")
        return create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db(target_engine=None):
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)

def get_db():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
