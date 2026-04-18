from datetime import datetime

from app.core.database import SessionLocal
from app.models.extracted_features import ExtractedFeatures
from app.models.risk_flag import RiskFlag
from app.repos.feature_repo import FeatureRepo
from app.repos.prediction_repo import PredictionRepo
from app.repos.session_repo import SessionRepo
from app.services.fraud_service import FraudService
from app.services.prediction_service import PredictionService
from app.utils.enums import PredictionStatus, SessionStatus
from app.workers.celery_app import celery_app
from app.workers.tasks_cv import extract_visual_features
from app.workers.tasks_explain import build_explanations
from app.workers.tasks_geo import enrich_geo_features


@celery_app.task(name="process_prediction_task")
def process_prediction_task(prediction_id: str):
    db = SessionLocal()
    try:
        prediction_repo = PredictionRepo(db)
        prediction = prediction_repo.get(prediction_id)
        if not prediction:
            return
        prediction.status = PredictionStatus.running.value
        db.add(prediction)
        db.commit()

        session = SessionRepo(db).get(prediction.session_id)
        if not session:
            prediction.status = PredictionStatus.failed.value
            db.add(prediction)
            db.commit()
            return

        visual_features, qc_features = extract_visual_features(session.id)
        geo_features = enrich_geo_features(session.id)
        feature_snapshot = FeatureRepo(db).create(
            ExtractedFeatures(
                session_id=session.id,
                model_version="feature-contract-v1",
                visual_features=visual_features,
                geo_features=geo_features,
                qc_features=qc_features,
                feature_vector={**visual_features, **geo_features, **qc_features, **(session.optional_inputs or {})},
                out_of_distribution_score=0.18,
            )
        )

        fraud_result = FraudService().evaluate(visual_features, geo_features, qc_features)
        result = PredictionService().score(
            prediction_id=prediction.id,
            visual_features=visual_features,
            geo_features=geo_features,
            qc_features=qc_features,
            anomaly_score=fraud_result.anomaly_score,
            flags=[{"code": flag.code, "severity": flag.severity.value} for flag in fraud_result.triggered_flags],
            optional_inputs=session.optional_inputs or {},
        )
        visual_features["detected_shop_type"] = result.detected_shop_type.value if result.detected_shop_type else None
        visual_features["shop_type_confirmed_by_user"] = result.shop_type_confirmed_by_user
        visual_features["shop_type_needs_confirmation"] = result.shop_type_needs_confirmation
        merchant_expl, underwriter_expl = build_explanations(prediction.id, visual_features, geo_features, result.confidence_score or 0.5)

        prediction.feature_snapshot_id = feature_snapshot.id
        prediction.status = PredictionStatus.completed.value
        prediction.daily_sales_min = result.daily_sales_range.min
        prediction.daily_sales_max = result.daily_sales_range.max
        prediction.monthly_revenue_min = result.monthly_revenue_range.min
        prediction.monthly_revenue_max = result.monthly_revenue_range.max
        prediction.monthly_income_min = result.monthly_income_range.min
        prediction.monthly_income_max = result.monthly_income_range.max
        prediction.confidence_score = result.confidence_score
        prediction.recommendation = result.recommendation.value if result.recommendation else None
        prediction.eligibility = result.eligibility.model_dump() if hasattr(result.eligibility, "model_dump") else result.eligibility
        prediction.benchmark = result.benchmark.model_dump() if hasattr(result.benchmark, "model_dump") else result.benchmark
        prediction.explanation_merchant = merchant_expl
        prediction.explanation_underwriter = underwriter_expl
        prediction.completed_at = datetime.utcnow()
        prediction_repo.save(prediction)

        session.optional_inputs = {
            **(session.optional_inputs or {}),
            "shop_type": result.detected_shop_type.value if result.detected_shop_type else None,
            "shop_type_confidence": result.shop_type_confidence,
            "shop_type_source": result.shop_type_source,
            "shop_type_needs_confirmation": result.shop_type_needs_confirmation,
            "shop_type_confirmed_by_user": result.shop_type_confirmed_by_user,
            "shop_type_candidates": [candidate.model_dump() for candidate in result.shop_type_candidates],
        }

        for flag in fraud_result.triggered_flags:
            db.add(
                RiskFlag(
                    prediction_id=prediction.id,
                    flag_code=flag.code,
                    severity=flag.severity.value,
                    source="rule",
                    details=flag.details,
                )
            )
        session.status = SessionStatus.completed.value
        db.add(session)
        db.commit()
    except Exception:
        prediction = PredictionRepo(db).get(prediction_id)
        if prediction:
            prediction.status = PredictionStatus.failed.value
            db.add(prediction)
            db.commit()
        raise
    finally:
        db.close()
