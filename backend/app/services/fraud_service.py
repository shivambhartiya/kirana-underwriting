from app.schemas.fraud import FraudCheckResponse, FraudFlag
from app.utils.enums import Recommendation, RiskSeverity
from app.utils.geo_math import clamp


class FraudService:
    def evaluate(self, visual_features: dict, geo_features: dict, qc_features: dict) -> FraudCheckResponse:
        flags: list[FraudFlag] = []
        if visual_features.get("inventory_value_proxy", 0) > 150000 and geo_features.get("footfall_proxy", 0) < 0.35:
            flags.append(FraudFlag(code="inventory_footfall_mismatch", severity=RiskSeverity.medium, details={}))
        alignment_gap = abs(visual_features.get("inventory_depth_score", 0.5) - geo_features.get("footfall_proxy", 0.5))
        if alignment_gap > 0.38:
            flags.append(
                FraudFlag(
                    code="visual_geo_discrepancy",
                    severity=RiskSeverity.medium,
                    details={"alignment_gap": round(alignment_gap, 2)},
                )
            )
        if qc_features.get("role_count", 0) < 3:
            flags.append(FraudFlag(code="limited_view_coverage", severity=RiskSeverity.low, details={}))
        if visual_features.get("shelf_density_index", 0) > 0.9:
            flags.append(FraudFlag(code="unrealistic_shelf_density", severity=RiskSeverity.high, details={}))
        if qc_features.get("duplicate_count", 0) > 0:
            flags.append(FraudFlag(code="duplicate_or_reused_images", severity=RiskSeverity.high, details={}))

        anomaly_score = round(clamp((len(flags) * 0.22) + (0.15 if qc_features.get("avg_quality_score", 1) < 0.5 else 0), 0.05, 0.95), 2)
        recommendation = Recommendation.needs_verification if flags else Recommendation.approve_candidate
        if anomaly_score > 0.65:
            recommendation = Recommendation.reject_candidate
        return FraudCheckResponse(anomaly_score=anomaly_score, recommendation=recommendation, triggered_flags=flags)
