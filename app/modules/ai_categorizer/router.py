import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.ai_categorizer.schemas import ExpenseRequest, ExpenseCategorizationResponse
from app.modules.ai_categorizer.service_v1 import CategorizerV1
from app.modules.ai_categorizer.service_v2 import CategorizerV2
from app.modules.feature_flags.repository import SQLAlchemyFeatureFlagRepository
from app.modules.feature_flags.service import FeatureFlagService
from app.modules.shadow.service import ShadowService

router = APIRouter(prefix="/api/v1", tags=["AI Categorizer"])

FEATURE_FLAG_NAME = "expense_categorizer"

@router.post("/categorize", response_model=ExpenseCategorizationResponse)
def categorize_expense(
    request: ExpenseRequest,
    db: Session = Depends(get_db)
):
    start_prod_time = time.perf_counter()

    # Initialize Feature Flag Service
    repo = SQLAlchemyFeatureFlagRepository(db_session=db)
    flag_service = FeatureFlagService(repository=repo)

    # Evaluate feature flag deterministically for the user
    eval_result = flag_service.evaluate_flag_for_user(
        feature_name=FEATURE_FLAG_NAME,
        user_id=request.user_id
    )

    # Instantiate categorizers
    v1_service = CategorizerV1()
    v2_service = CategorizerV2()

    # Route execution based on feature flag evaluation assignment for production response
    if eval_result.is_experiment and eval_result.assigned_version == v2_service.VERSION_NAME:
        prod_response = v2_service.categorize(
            description=request.description,
            amount=request.amount,
            is_experiment=True
        )
    else:
        prod_response = v1_service.categorize(
            description=request.description,
            amount=request.amount,
            is_experiment=False
        )

    prod_latency_ms = (time.perf_counter() - start_prod_time) * 1000.0

    # Shadow Mode Background Execution (Non-intrusive to production response)
    shadow_svc = ShadowService()
    if shadow_svc.is_shadow_enabled(db, FEATURE_FLAG_NAME):
        shadow_svc.execute_shadow_evaluation(
            db=db,
            feature_name=FEATURE_FLAG_NAME,
            user_id=request.user_id,
            description=request.description,
            amount=request.amount,
            prod_version=prod_response.assigned_version,
            prod_category=prod_response.category,
            prod_latency_ms=prod_latency_ms
        )

    return prod_response
