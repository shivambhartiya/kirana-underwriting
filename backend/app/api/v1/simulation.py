from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import DbSession, get_current_user
from app.repos.prediction_repo import PredictionRepo
from app.repos.session_repo import SessionRepo
from app.schemas.simulation import SimulationRequest, SimulationResponse
from app.services.simulation_service import SimulationService


router = APIRouter()


@router.post("/simulate", response_model=SimulationResponse)
def simulate(payload: SimulationRequest, db: DbSession, user=Depends(get_current_user)):
    prediction = PredictionRepo(db).get(payload.prediction_id)
    if not prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    session = SessionRepo(db).get(prediction.session_id)
    if not session or (user.role == "merchant" and session.user_id != user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    base_ranges = {
        "daily_sales": (float(prediction.daily_sales_min or 0), float(prediction.daily_sales_max or 0)),
        "monthly_revenue": (float(prediction.monthly_revenue_min or 0), float(prediction.monthly_revenue_max or 0)),
        "monthly_income": (float(prediction.monthly_income_min or 0), float(prediction.monthly_income_max or 0)),
    }
    delta_multiplier = 1 + payload.delta_shelf_density + payload.delta_storefront_visibility + payload.delta_footfall_proxy
    return SimulationService().simulate(payload.prediction_id, base_ranges, max(0.6, min(delta_multiplier, 1.8)))

