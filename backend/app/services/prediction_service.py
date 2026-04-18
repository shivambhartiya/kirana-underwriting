from datetime import datetime, timezone

from app.schemas.common import MoneyRange
from app.schemas.prediction import PredictionResultResponse, RiskFlagResponse
from app.schemas.upload import ShopTypeCandidate
from app.services.benchmark_service import BenchmarkService
from app.services.eligibility_service import EligibilityService
from app.utils.confidence import compute_confidence
from app.utils.enums import PredictionStatus, Recommendation, RiskSeverity, ShopType
from app.utils.geo_math import clamp, interpolate
from ml.inference.range_model import HybridRangeModel


class PredictionService:
    underwriting_model_version = "lgbm-quantile-v1.5-calibrated"
    shop_type_profiles = {
        ShopType.kirana_general: {
            "daily_customers": (42, 120),
            "basket_value": (130, 300),
            "gross_margin": (0.10, 0.16),
            "opex_rate": (0.025, 0.06),
            "fixed_opex_base": 8500,
            "monthly_revenue_per_sqft_cap": 3600,
        },
        ShopType.vegetable_fruit: {
            "daily_customers": (55, 135),
            "basket_value": (70, 170),
            "gross_margin": (0.09, 0.14),
            "opex_rate": (0.03, 0.065),
            "fixed_opex_base": 7800,
            "monthly_revenue_per_sqft_cap": 3200,
        },
        ShopType.pharmacy_medical: {
            "daily_customers": (24, 68),
            "basket_value": (180, 480),
            "gross_margin": (0.13, 0.22),
            "opex_rate": (0.03, 0.07),
            "fixed_opex_base": 9500,
            "monthly_revenue_per_sqft_cap": 4300,
        },
        ShopType.fast_food_qsr: {
            "daily_customers": (60, 170),
            "basket_value": (90, 230),
            "gross_margin": (0.16, 0.24),
            "opex_rate": (0.05, 0.11),
            "fixed_opex_base": 14000,
            "monthly_revenue_per_sqft_cap": 4700,
        },
        ShopType.religious_gifts: {
            "daily_customers": (10, 34),
            "basket_value": (130, 420),
            "gross_margin": (0.18, 0.28),
            "opex_rate": (0.03, 0.07),
            "fixed_opex_base": 7600,
            "monthly_revenue_per_sqft_cap": 2600,
        },
        ShopType.jewellery: {
            "daily_customers": (3, 12),
            "basket_value": (2200, 12000),
            "gross_margin": (0.15, 0.24),
            "opex_rate": (0.04, 0.09),
            "fixed_opex_base": 18000,
            "monthly_revenue_per_sqft_cap": 9000,
        },
        ShopType.bakery_sweets: {
            "daily_customers": (48, 125),
            "basket_value": (95, 240),
            "gross_margin": (0.14, 0.21),
            "opex_rate": (0.04, 0.09),
            "fixed_opex_base": 9800,
            "monthly_revenue_per_sqft_cap": 3900,
        },
        ShopType.mobile_electronics: {
            "daily_customers": (6, 24),
            "basket_value": (550, 3800),
            "gross_margin": (0.09, 0.16),
            "opex_rate": (0.03, 0.08),
            "fixed_opex_base": 11000,
            "monthly_revenue_per_sqft_cap": 5200,
        },
        ShopType.apparel_boutique: {
            "daily_customers": (8, 28),
            "basket_value": (450, 1800),
            "gross_margin": (0.18, 0.3),
            "opex_rate": (0.04, 0.1),
            "fixed_opex_base": 10500,
            "monthly_revenue_per_sqft_cap": 4200,
        },
    }
    specialty_blended_profile = {
        "daily_customers": (12, 42),
        "basket_value": (150, 520),
        "gross_margin": (0.12, 0.21),
        "opex_rate": (0.035, 0.08),
        "fixed_opex_base": 9000,
        "monthly_revenue_per_sqft_cap": 3100,
    }

    def __init__(self):
        self.eligibility_service = EligibilityService()
        self.benchmark_service = BenchmarkService()
        self.range_model = HybridRangeModel()

    def score(
        self,
        prediction_id: str,
        visual_features: dict,
        geo_features: dict,
        qc_features: dict,
        anomaly_score: float,
        flags: list[dict],
        optional_inputs: dict | None = None,
    ) -> PredictionResultResponse:
        optional_inputs = optional_inputs or {}
        raw_shop_type = optional_inputs.get("shop_type", ShopType.kirana_general.value)
        try:
            detected_shop_type = ShopType(raw_shop_type)
        except ValueError:
            detected_shop_type = ShopType.kirana_general

        shop_type_confidence = float(optional_inputs.get("shop_type_confidence") or 0.58)
        shop_type_source = optional_inputs.get("shop_type_source") or "system_prior"
        shop_type_needs_confirmation = bool(optional_inputs.get("shop_type_needs_confirmation") or False)
        shop_type_confirmed_by_user = bool(optional_inputs.get("shop_type_confirmed_by_user") or False)
        raw_candidates = optional_inputs.get("shop_type_candidates") or []
        shop_type_candidates = [
            candidate if isinstance(candidate, ShopTypeCandidate) else ShopTypeCandidate.model_validate(candidate)
            for candidate in raw_candidates
        ]
        if not shop_type_candidates:
            shop_type_candidates = [
                ShopTypeCandidate(
                    shop_type=detected_shop_type,
                    confidence=round(shop_type_confidence, 2),
                    reasons=["Selected directly or inferred without alternatives."],
                )
            ]

        if shop_type_needs_confirmation and not shop_type_confirmed_by_user:
            profile = self.specialty_blended_profile
            effective_shop_type_confidence = min(shop_type_confidence, 0.5)
            effective_shop_type_source = f"{shop_type_source}_blended_prior"
            flags = [*flags, {"code": "shop_type_needs_confirmation", "severity": "medium"}]
        else:
            profile = self.shop_type_profiles[detected_shop_type]
            effective_shop_type_confidence = shop_type_confidence
            effective_shop_type_source = shop_type_source

        shop_size_sqft = float(optional_inputs.get("shop_size_sqft") or visual_features.get("visual_store_size_sqft_proxy", 140))
        monthly_rent = float(optional_inputs.get("monthly_rent") or 12000)
        years_in_operation = float(optional_inputs.get("years_in_operation") or 2)
        video_duration_seconds = float(optional_inputs.get("video_duration_seconds") or 0)

        demand = geo_features.get("footfall_proxy", 0.42)
        catchment = geo_features.get("catchment_density", 0.45)
        inventory = visual_features.get("inventory_depth_score", 0.42)
        diversity = visual_features.get("sku_diversity_score", 0.38)
        visibility = visual_features.get("storefront_visibility_score", 0.46)
        merchandising = visual_features.get("merchandising_quality_score", 0.44)
        refill_signal = visual_features.get("refill_signal", 0.28)
        competition_count = geo_features.get("competition_count_500m", 4)
        commercial_mix = geo_features.get("commercial_mix", 0.35)
        geo_confidence = geo_features.get("geo_source_confidence", 0.68)
        image_quality = qc_features.get("avg_quality_score", 0.72)
        operating_days = 30

        size_factor = clamp((shop_size_sqft / 180) ** 0.45, 0.7, 1.55)
        stability_factor = clamp(0.92 + (min(years_in_operation, 15) * 0.012), 0.92, 1.12)
        competition_penalty = clamp(competition_count / 22, 0.03, 0.32)
        video_confidence_boost = 0.04 if 5 <= video_duration_seconds <= 10 else 0.0

        traffic_score = clamp(
            (demand * 0.34)
            + (catchment * 0.22)
            + (visibility * 0.14)
            + (merchandising * 0.12)
            + (refill_signal * 0.08)
            + (commercial_mix * 0.10)
            - competition_penalty,
            0.08,
            0.94,
        )
        basket_score = clamp(
            (diversity * 0.35)
            + (inventory * 0.18)
            + (commercial_mix * 0.18)
            + (demand * 0.14)
            + (visibility * 0.15),
            0.08,
            0.95,
        )

        daily_customers = interpolate(*profile["daily_customers"], traffic_score) * size_factor * stability_factor
        average_basket = interpolate(*profile["basket_value"], basket_score)
        rule_daily_sales_mid = daily_customers * average_basket

        ml_ranges = self.range_model.predict(
            {
                **visual_features,
                **geo_features,
                **qc_features,
                "shop_type": detected_shop_type.value,
            }
        )
        ml_daily = ml_ranges["daily_sales"]
        daily_sales_mid = (rule_daily_sales_mid * 0.82) + (ml_daily.median * 0.18)

        monthly_revenue_cap = shop_size_sqft * profile["monthly_revenue_per_sqft_cap"] * interpolate(0.86, 1.12, demand)
        monthly_revenue_floor = shop_size_sqft * interpolate(240, 640, traffic_score)
        capped_daily_mid = clamp(daily_sales_mid, monthly_revenue_floor / operating_days, monthly_revenue_cap / operating_days)

        discrepancy_penalty = abs((inventory + merchandising) / 2 - demand) + (0.35 * abs(visibility - geo_features.get("road_class_score", 0.5)))
        spread = clamp(
            0.14
            + (0.14 * discrepancy_penalty)
            + (0.12 * anomaly_score)
            + (0.08 * (1 - image_quality))
            + (0.06 * (1 - geo_confidence)),
            0.12,
            0.34,
        )
        daily_sales_min = capped_daily_mid * (1 - spread)
        daily_sales_max = capped_daily_mid * (1 + spread)
        monthly_revenue_min = max(daily_sales_min * operating_days, monthly_revenue_floor * 0.72)
        monthly_revenue_max = min(daily_sales_max * operating_days, monthly_revenue_cap)
        if monthly_revenue_max <= monthly_revenue_min:
            monthly_revenue_max = monthly_revenue_min * 1.16

        margin_score = clamp((diversity * 0.34) + (merchandising * 0.24) + (commercial_mix * 0.18) + (effective_shop_type_confidence * 0.24), 0.08, 0.95)
        gross_margin_rate = interpolate(*profile["gross_margin"], margin_score)
        opex_rate = interpolate(*profile["opex_rate"], clamp(1 - image_quality + competition_penalty, 0.05, 0.95))
        fixed_opex = profile["fixed_opex_base"] + monthly_rent + (shop_size_sqft * 10) + (1200 if detected_shop_type == ShopType.fast_food_qsr else 0)
        fixed_opex *= interpolate(0.96, 1.06, 1 - clamp(years_in_operation / 12, 0.0, 1.0))

        monthly_income_min = max((monthly_revenue_min * (gross_margin_rate - 0.02)) - fixed_opex - (monthly_revenue_min * (opex_rate + 0.01)), 2500)
        monthly_income_max = max(
            (monthly_revenue_max * (gross_margin_rate + 0.015)) - fixed_opex - (monthly_revenue_max * max(opex_rate - 0.008, 0.01)),
            monthly_income_min + 2500,
        )
        monthly_income_max = min(monthly_income_max, monthly_revenue_max * 0.22)

        annual_revenue_min = monthly_revenue_min * 12
        annual_revenue_max = monthly_revenue_max * 12
        annual_income_min = monthly_income_min * 12
        annual_income_max = monthly_income_max * 12

        interval_width_ratio = (daily_sales_max - daily_sales_min) / max(capped_daily_mid, 1)
        completeness = clamp((qc_features.get("role_count", 0) / 4), 0.25, 1.0)
        confidence = compute_confidence(
            interval_width_ratio
            + (0.15 * discrepancy_penalty)
            + (0.08 * (1 - effective_shop_type_confidence))
            + (0.05 * (1 - geo_confidence)),
            completeness,
            anomaly_score,
            min(1.0, image_quality + video_confidence_boost),
        )

        recommendation = Recommendation.needs_verification if flags else Recommendation.approve_candidate
        if anomaly_score > 0.65:
            recommendation = Recommendation.reject_candidate
        elif shop_type_needs_confirmation and not shop_type_confirmed_by_user:
            recommendation = Recommendation.needs_verification

        benchmark = self.benchmark_service.benchmark((monthly_revenue_min + monthly_revenue_max) / 2, geo_features)
        eligibility = self.eligibility_service.suggest(monthly_income_min, monthly_income_max)
        risk_flags = [RiskFlagResponse(code=flag["code"], severity=RiskSeverity(flag["severity"])) for flag in flags]

        return PredictionResultResponse(
            prediction_id=prediction_id,
            status=PredictionStatus.completed,
            detected_shop_type=detected_shop_type,
            shop_type_confidence=round(effective_shop_type_confidence, 2),
            shop_type_source=effective_shop_type_source,
            shop_type_candidates=shop_type_candidates,
            shop_type_needs_confirmation=shop_type_needs_confirmation,
            shop_type_confirmed_by_user=shop_type_confirmed_by_user,
            daily_sales_range=MoneyRange(min=round(daily_sales_min, 2), max=round(daily_sales_max, 2)),
            monthly_revenue_range=MoneyRange(min=round(monthly_revenue_min, 2), max=round(monthly_revenue_max, 2)),
            monthly_income_range=MoneyRange(min=round(monthly_income_min, 2), max=round(monthly_income_max, 2)),
            annual_revenue_run_rate=MoneyRange(min=round(annual_revenue_min, 2), max=round(annual_revenue_max, 2)),
            annual_income_run_rate=MoneyRange(min=round(annual_income_min, 2), max=round(annual_income_max, 2)),
            confidence_score=confidence,
            risk_flags=risk_flags,
            recommendation=recommendation,
            eligibility=eligibility,
            benchmark=benchmark,
            model_versions={
                "vision": "yolov8-kirana-v1",
                "geo": "geo-features-v2-live-context",
                "underwriting": self.underwriting_model_version,
            },
            created_at=datetime.now(timezone.utc),
        )
