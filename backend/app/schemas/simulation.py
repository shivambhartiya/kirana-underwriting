from pydantic import BaseModel

from app.schemas.common import MoneyRange


class SimulationRequest(BaseModel):
    prediction_id: str
    delta_shelf_density: float = 0.0
    delta_storefront_visibility: float = 0.0
    delta_footfall_proxy: float = 0.0


class SimulationResponse(BaseModel):
    prediction_id: str
    revised_daily_sales_range: MoneyRange
    revised_monthly_revenue_range: MoneyRange
    revised_monthly_income_range: MoneyRange
    summary: str

