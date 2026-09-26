from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.ai_categorizer.schemas import ExpenseRequest, ExpenseCategorizationResponse
from app.modules.ai_categorizer.service_v1 import CategorizerV1
from app.modules.ai_categorizer.service_v2 import CategorizerV2
from app.modules.feature_flags.repository import SQLAlchemyFeatureFlagRepository
from app.modules.feature_flags.service import FeatureFlagService

router = APIRouter(prefix="/api/v1", tags=["AI Categorizer"])

FEATURE_FLAG_NAME = "expense_categorizer"

@router.post("/categorize", response_model=ExpenseCategorizationResponse)
def categorize_expense(
    request: ExpenseRequest,
    db: Session = Depends(get_db)
):
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

    # Route execution based on feature flag evaluation assignment
    if eval_result.is_experiment and eval_result.assigned_version == v2_service.VERSION_NAME:
        return v2_service.categorize(
            description=request.description,
            amount=request.amount,
            is_experiment=True
        )
    else:
        return v1_service.categorize(
            description=request.description,
            amount=request.amount,
            is_experiment=False
        )
