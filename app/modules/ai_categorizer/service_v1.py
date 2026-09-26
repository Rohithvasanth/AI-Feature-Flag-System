from app.modules.ai_categorizer.schemas import ExpenseCategorizationResponse

class CategorizerV1:
    """
    Version A: Basic Rule-Based Expense Categorizer (v1.0)
    """
    VERSION_NAME = "categorizer_v1"

    def categorize(self, description: str, amount: float, is_experiment: bool = False) -> ExpenseCategorizationResponse:
        desc_lower = description.lower()

        if any(w in desc_lower for w in ["starbucks", "coffee", "lunch", "restaurant", "burger", "pizza", "cafe"]):
            category = "Food & Dining"
            subcategory = "Dining"
            confidence = 0.70
        elif any(w in desc_lower for w in ["uber", "lyft", "flight", "taxi", "gas", "fuel", "airline"]):
            category = "Transportation"
            subcategory = "Transit"
            confidence = 0.70
        elif any(w in desc_lower for w in ["aws", "github", "zoom", "slack", "cloud", "server"]):
            category = "Software & Services"
            subcategory = "Subscriptions"
            confidence = 0.70
        elif any(w in desc_lower for w in ["staples", "paper", "desk", "printer", "office"]):
            category = "Office Supplies"
            subcategory = "Supplies"
            confidence = 0.70
        else:
            category = "Uncategorized"
            subcategory = "General"
            confidence = 0.50

        # Basic merchant extraction (first word capitalized)
        words = description.split()
        merchant = words[0].capitalize() if words else "Unknown"

        return ExpenseCategorizationResponse(
            description=description,
            amount=amount,
            category=category,
            subcategory=subcategory,
            confidence=confidence,
            assigned_version=self.VERSION_NAME,
            is_experiment=is_experiment,
            merchant=merchant
        )
