from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import DbSession, get_current_user
from app.repos.feature_repo import FeatureRepo
from app.repos.prediction_repo import PredictionRepo
from app.repos.session_repo import SessionRepo
from app.schemas.explain import ExplainRequest, ExplainResponse
from app.services.explain_service import ExplainService


router = APIRouter()


@router.post("/explain", response_model=ExplainResponse)
def explain(payload: ExplainRequest, db: DbSession, user=Depends(get_current_user)):
    prediction = PredictionRepo(db).get(payload.prediction_id)
    if not prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    session = SessionRepo(db).get(prediction.session_id)
    if not session or (user.role == "merchant" and session.user_id != user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    features = FeatureRepo(db).get_latest_for_session(session.id)
    if not features:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Features not found")
    return ExplainService().generate(payload.prediction_id, features.visual_features, features.geo_features, prediction.confidence_score or 0.5, payload.audience)

