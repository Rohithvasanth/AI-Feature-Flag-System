from pydantic import BaseModel, Field
from typing import Optional

class ExpenseRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    description: str = Field(..., description="Expense item description")
    amount: float = Field(..., ge=0.0, description="Expense amount in USD")

class ExpenseCategorizationResponse(BaseModel):
    description: str
    amount: float
    category: str
    subcategory: Optional[str] = "General"
    confidence: float
    assigned_version: str
    is_experiment: bool
    merchant: Optional[str] = "Unknown"
