from app.services.explain_service import ExplainService
from app.utils.enums import ExplainAudience


def build_explanations(prediction_id: str, visual_features: dict, geo_features: dict, confidence_score: float) -> tuple[str, str]:
    service = ExplainService()
    merchant = service.generate(prediction_id, visual_features, geo_features, confidence_score, ExplainAudience.merchant)
    underwriter = service.generate(prediction_id, visual_features, geo_features, confidence_score, ExplainAudience.underwriter)
    return merchant.narrative, underwriter.narrative

