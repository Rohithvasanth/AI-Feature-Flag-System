from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db
from app.modules.feature_flags.router import router as flags_router
from app.modules.ai_categorizer.router import router as categorizer_router
from app.modules.quality.router import router as quality_router
from app.modules.monitoring.router import router as monitoring_router
from app.modules.rollback.router import router as rollback_router
from app.modules.rollout.router import router as rollout_router
from app.modules.dashboard.router import router as dashboard_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="AI Feature Flag System backend API",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Register API Routers
app.include_router(flags_router)
app.include_router(categorizer_router)
app.include_router(quality_router)
app.include_router(monitoring_router)
app.include_router(rollback_router)
app.include_router(rollout_router)
app.include_router(dashboard_router)

@app.get("/")
def read_root():
    return {"message": "AI Feature Flag System backend is running"}

@app.get("/health")
def read_health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
