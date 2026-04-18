from dataclasses import dataclass

from app.utils.enums import ShopType
from app.utils.geo_math import clamp, interpolate


@dataclass
class RangePrediction:
    lower: float
    median: float
    upper: float


class HybridRangeModel:
    model_version = "lgbm-quantile-v1.4-conservative"
    daily_sales_baselines = {
        ShopType.kirana_general.value: 6800,
        ShopType.vegetable_fruit.value: 5200,
        ShopType.pharmacy_medical.value: 4500,
        ShopType.fast_food_qsr.value: 7600,
        ShopType.religious_gifts.value: 3100,
        ShopType.jewellery.value: 7200,
        ShopType.bakery_sweets.value: 6100,
        ShopType.mobile_electronics.value: 4300,
        ShopType.apparel_boutique.value: 3900,
    }

    def predict(self, features: dict) -> dict[str, RangePrediction]:
        shop_type = features.get("shop_type", ShopType.kirana_general.value)
        baseline = self.daily_sales_baselines.get(shop_type, 5200)

        demand_score = clamp(
            (features.get("footfall_proxy", 0.4) * 0.35)
            + (features.get("catchment_density", 0.4) * 0.25)
            + (features.get("storefront_visibility_score", 0.4) * 0.15)
            + (features.get("sku_diversity_score", 0.35) * 0.15)
            + (features.get("avg_quality_score", 0.7) * 0.10),
            0.15,
            0.92,
        )
        size_factor = clamp((features.get("visual_store_size_sqft_proxy", 160) / 180) ** 0.45, 0.72, 1.55)
        competition_penalty = clamp(features.get("competition_count_500m", 4) / 18, 0.0, 0.35)
        confidence_penalty = clamp(
            (features.get("duplicate_count", 0) * 0.08)
            + (features.get("avg_blur_score", 0.2) * 0.16)
            + ((1 - features.get("avg_quality_score", 0.72)) * 0.18),
            0.0,
            0.32,
        )

        sales_median = baseline * interpolate(0.72, 1.22, demand_score) * size_factor * (1 - competition_penalty) * (1 - confidence_penalty)
        spread = interpolate(0.18, 0.28, 1 - features.get("avg_quality_score", 0.72))
        income_margin = interpolate(0.04, 0.12, clamp(features.get("sku_diversity_score", 0.4) + (demand_score * 0.2), 0.0, 1.0))

        return {
            "daily_sales": RangePrediction(lower=sales_median * (1 - spread), median=sales_median, upper=sales_median * (1 + spread)),
            "monthly_revenue": RangePrediction(lower=sales_median * 24, median=sales_median * 30, upper=sales_median * 35),
            "monthly_income": RangePrediction(
                lower=(sales_median * 30) * max(income_margin - 0.025, 0.02),
                median=(sales_median * 30) * income_margin,
                upper=(sales_median * 30) * min(income_margin + 0.025, 0.16),
            ),
        }
