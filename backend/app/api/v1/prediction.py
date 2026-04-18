from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import DbSession, get_current_user
from app.core.config import get_settings
from app.models.audit_log import AuditLog
from app.models.prediction import Prediction
from app.repos.audit_repo import AuditRepo
from app.repos.prediction_repo import PredictionRepo
from app.repos.session_repo import SessionRepo
from app.schemas.prediction import PredictRequest, PredictResponse, PredictionResultResponse
from app.schemas.upload import ShopTypeCandidate
from app.utils.enums import PredictionStatus, SessionStatus
from app.workers.tasks_predict import process_prediction_task


router = APIRouter()
settings = get_settings()


@router.post("/predict", response_model=PredictResponse)
def create_prediction(payload: PredictRequest, db: DbSession, user=Depends(get_current_user)):
    session = SessionRepo(db).get(payload.session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.status not in [SessionStatus.located.value, SessionStatus.processing.value, SessionStatus.completed.value]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload and location steps must be complete")

    if payload.optional_inputs:
        session.optional_inputs = payload.optional_inputs.model_dump(exclude_none=True)
        db.add(session)
        db.commit()

    prediction = Prediction(
        session_id=session.id,
        underwriting_model_version="lgbm-quantile-v1.3",
        status=PredictionStatus.queued.value,
    )
    prediction = PredictionRepo(db).create(prediction)
    session.status = SessionStatus.processing.value
    db.add(session)
    db.commit()
    AuditRepo(db).create(
        AuditLog(
            user_id=user.id,
            session_id=session.id,
            prediction_id=prediction.id,
            action="prediction_queued",
            entity_type="prediction",
            entity_id=prediction.id,
        )
    )
    try:
        if settings.enable_local_sync_jobs:
            process_prediction_task(prediction.id)
        else:
            process_prediction_task.delay(prediction.id)
    except Exception:
        process_prediction_task(prediction.id)
    refreshed = PredictionRepo(db).get(prediction.id)
    status_value = PredictionStatus(refreshed.status if refreshed else prediction.status)
    return PredictResponse(prediction_id=prediction.id, status=status_value)


@router.get("/predict/{prediction_id}", response_model=PredictionResultResponse)
def get_prediction(prediction_id: str, db: DbSession, user=Depends(get_current_user)):
    prediction = PredictionRepo(db).get(prediction_id)
    if not prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    session = SessionRepo(db).get(prediction.session_id)
    if not session or (user.role == "merchant" and session.user_id != user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    flags = PredictionRepo(db).list_flags(prediction.id)
    optional_inputs = session.optional_inputs or {}
    candidate_payload = [
        candidate if isinstance(candidate, ShopTypeCandidate) else ShopTypeCandidate.model_validate(candidate)
        for candidate in optional_inputs.get("shop_type_candidates", [])
    ]
    monthly_revenue_range = None if prediction.monthly_revenue_min is None else {"min": float(prediction.monthly_revenue_min), "max": float(prediction.monthly_revenue_max), "currency": "INR"}
    monthly_income_range = None if prediction.monthly_income_min is None else {"min": float(prediction.monthly_income_min), "max": float(prediction.monthly_income_max), "currency": "INR"}
    return PredictionResultResponse(
        prediction_id=prediction.id,
        status=PredictionStatus(prediction.status),
        detected_shop_type=getattr(prediction, "detected_shop_type", None) or optional_inputs.get("shop_type"),
        shop_type_confidence=optional_inputs.get("shop_type_confidence"),
        shop_type_source=optional_inputs.get("shop_type_source"),
        shop_type_candidates=candidate_payload,
        shop_type_needs_confirmation=bool(optional_inputs.get("shop_type_needs_confirmation") or False),
        shop_type_confirmed_by_user=bool(optional_inputs.get("shop_type_confirmed_by_user") or False),
        daily_sales_range=None if prediction.daily_sales_min is None else {"min": float(prediction.daily_sales_min), "max": float(prediction.daily_sales_max), "currency": "INR"},
        monthly_revenue_range=monthly_revenue_range,
        monthly_income_range=monthly_income_range,
        annual_revenue_run_rate=None if prediction.monthly_revenue_min is None else {"min": float(prediction.monthly_revenue_min) * 12, "max": float(prediction.monthly_revenue_max) * 12, "currency": "INR"},
        annual_income_run_rate=None if prediction.monthly_income_min is None else {"min": float(prediction.monthly_income_min) * 12, "max": float(prediction.monthly_income_max) * 12, "currency": "INR"},
        confidence_score=prediction.confidence_score,
        risk_flags=[{"code": flag.flag_code, "severity": flag.severity} for flag in flags],
        recommendation=prediction.recommendation,
        eligibility=prediction.eligibility,
        benchmark=prediction.benchmark,
        model_versions={"vision": "yolov8-kirana-v1", "geo": "geo-features-v1", "underwriting": prediction.underwriting_model_version},
        explanation_merchant=prediction.explanation_merchant,
        explanation_underwriter=prediction.explanation_underwriter,
        created_at=prediction.created_at or datetime.utcnow(),
    )
