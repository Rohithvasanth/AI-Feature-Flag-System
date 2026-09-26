import re
from app.modules.ai_categorizer.schemas import ExpenseCategorizationResponse

class CategorizerV2:
    """
    Version B: Improved AI-Based Expense Categorizer (v2.0)
    Uses advanced pattern recognition, merchant extraction, and amount context.
    """
    VERSION_NAME = "categorizer_v2"

    def categorize(self, description: str, amount: float, is_experiment: bool = True) -> ExpenseCategorizationResponse:
        desc_lower = description.lower()

        # Merchant extraction using regex patterns
        merchant = self._extract_merchant(description)

        # Advanced classification logic with amount context
        if any(w in desc_lower for w in ["starbucks", "coffee", "cafe", "espresso"]):
            category = "Food & Dining"
            subcategory = "Coffee & Cafes"
            confidence = 0.96
        elif any(w in desc_lower for w in ["uber", "lyft", "grab", "taxi"]):
            category = "Transportation"
            subcategory = "Rideshare"
            confidence = 0.98
        elif any(w in desc_lower for w in ["flight", "airline", "delta", "united"]):
            category = "Transportation"
            subcategory = "Air Travel"
            confidence = 0.95
        elif any(w in desc_lower for w in ["aws", "azure", "google cloud", "cloud"]):
            category = "Software & Infrastructure"
            subcategory = "Cloud Compute & Hosting"
            confidence = 0.97
        elif any(w in desc_lower for w in ["github", "gitlab", "jira", "slack", "zoom"]):
            category = "Software & Infrastructure"
            subcategory = "SaaS Subscriptions"
            confidence = 0.96
        elif any(w in desc_lower for w in ["staples", "paper", "laptop", "monitor", "keyboard", "desk", "printer"]):
            if amount > 300.0:
                category = "Equipment & Hardware"
                subcategory = "IT Equipment"
                confidence = 0.94
            else:
                category = "Office Supplies"
                subcategory = "Stationery & Supplies"
                confidence = 0.92
        elif any(w in desc_lower for w in ["lunch", "dinner", "restaurant", "bistro", "burger", "pizza"]):
            category = "Food & Dining"
            subcategory = "Meals & Entertainment"
            confidence = 0.93
        else:
            category = "Business Operations"
            subcategory = "Miscellaneous Expenses"
            confidence = 0.85

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

    def _extract_merchant(self, description: str) -> str:
        # Remove common store numbers, locations, and transaction IDs
        cleaned = re.sub(r'#\d+|\bSQ\b|\*|\d{3,}', '', description).strip()
        words = cleaned.split()
        if words:
            return words[0].title()
        return "Unknown"
