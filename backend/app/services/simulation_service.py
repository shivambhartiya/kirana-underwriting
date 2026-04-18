from app.schemas.common import MoneyRange
from app.schemas.simulation import SimulationResponse


class SimulationService:
    def simulate(self, prediction_id: str, base_ranges: dict[str, tuple[float, float]], delta_multiplier: float) -> SimulationResponse:
        def scaled(range_pair: tuple[float, float]) -> MoneyRange:
            return MoneyRange(min=round(range_pair[0] * delta_multiplier, 2), max=round(range_pair[1] * delta_multiplier, 2))

        return SimulationResponse(
            prediction_id=prediction_id,
            revised_daily_sales_range=scaled(base_ranges["daily_sales"]),
            revised_monthly_revenue_range=scaled(base_ranges["monthly_revenue"]),
            revised_monthly_income_range=scaled(base_ranges["monthly_income"]),
            summary="Scenario assumes uplift from better merchandising, visibility, or footfall conditions.",
        )

