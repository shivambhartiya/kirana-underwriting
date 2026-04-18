from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import DbSession, get_current_user
from app.repos.feature_repo import FeatureRepo
from app.repos.prediction_repo import PredictionRepo
from app.repos.session_repo import SessionRepo
from app.schemas.fraud import FraudCheckRequest, FraudCheckResponse
from app.services.fraud_service import FraudService


router = APIRouter()


@router.post("/fraud-check", response_model=FraudCheckResponse)
def fraud_check(payload: FraudCheckRequest, db: DbSession, user=Depends(get_current_user)):
    prediction = PredictionRepo(db).get(payload.prediction_id) if payload.prediction_id else None
    session_id = payload.session_id or (prediction.session_id if prediction else None)
    if not session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="prediction_id or session_id is required")
    session = SessionRepo(db).get(session_id)
    if not session or (user.role == "merchant" and session.user_id != user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    features = FeatureRepo(db).get_latest_for_session(session_id)
    if not features:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Features not found")
    return FraudService().evaluate(features.visual_features, features.geo_features, features.qc_features)

