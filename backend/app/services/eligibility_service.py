from app.schemas.common import MoneyRange


class EligibilityService:
    def suggest(self, monthly_income_min: float, monthly_income_max: float) -> dict:
        safe_income = monthly_income_min * 0.35
        loan_min = max(50000.0, monthly_income_min * 3.2)
        loan_max = max(loan_min, monthly_income_max * 4.8)
        return {
            "suggested_loan_amount_range": MoneyRange(min=round(loan_min, 2), max=round(loan_max, 2)).model_dump(),
            "max_safe_emi": round(safe_income, 2),
            "suggested_tenure_months": 24,
        }

