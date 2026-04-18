from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import DbSession, get_current_user
from app.repos.prediction_repo import PredictionRepo
from app.repos.session_repo import SessionRepo


router = APIRouter()


@router.get("/benchmark/{prediction_id}")
def get_benchmark(prediction_id: str, db: DbSession, user=Depends(get_current_user)):
    prediction = PredictionRepo(db).get(prediction_id)
    if not prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    session = SessionRepo(db).get(prediction.session_id)
    if not session or (user.role == "merchant" and session.user_id != user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return prediction.benchmark or {}

