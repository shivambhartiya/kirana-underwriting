from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.prediction_service import PredictionService


def _base_inputs(shop_type: str, confirmed: bool = True, needs_confirmation: bool = False):
    return {
        "shop_type": shop_type,
        "shop_size_sqft": 180,
        "monthly_rent": 15000,
        "years_in_operation": 6,
        "shop_type_confidence": 0.78,
        "shop_type_source": "test_case",
        "shop_type_candidates": [{"shop_type": shop_type, "confidence": 0.78, "reasons": ["test"]}],
        "shop_type_confirmed_by_user": confirmed,
        "shop_type_needs_confirmation": needs_confirmation,
    }


def test_shop_type_priors_change_underwriting_ranges():
    service = PredictionService()
    visual_features = {
        "inventory_depth_score": 0.56,
        "sku_diversity_score": 0.48,
        "storefront_visibility_score": 0.71,
        "merchandising_quality_score": 0.63,
        "refill_signal": 0.36,
        "visual_store_size_sqft_proxy": 180,
    }
    geo_features = {
        "footfall_proxy": 0.54,
        "catchment_density": 0.62,
        "competition_count_500m": 4,
        "commercial_mix": 0.49,
        "road_class_score": 0.68,
    }
    qc_features = {"role_count": 4, "avg_quality_score": 0.81}

    religious = service.score("pred-1", visual_features, geo_features, qc_features, 0.08, [], _base_inputs("religious_gifts"))
    pharmacy = service.score("pred-2", visual_features, geo_features, qc_features, 0.08, [], _base_inputs("pharmacy_medical"))

    assert religious.monthly_revenue_range.min != pharmacy.monthly_revenue_range.min
    assert religious.monthly_income_range.max != pharmacy.monthly_income_range.max
    assert religious.monthly_income_range.max < pharmacy.monthly_income_range.max


def test_unconfirmed_shop_type_uses_conservative_blended_prior_and_flag():
    service = PredictionService()
    visual_features = {
        "inventory_depth_score": 0.52,
        "sku_diversity_score": 0.44,
        "storefront_visibility_score": 0.66,
        "merchandising_quality_score": 0.58,
        "refill_signal": 0.31,
        "visual_store_size_sqft_proxy": 165,
    }
    geo_features = {
        "footfall_proxy": 0.49,
        "catchment_density": 0.58,
        "competition_count_500m": 5,
        "commercial_mix": 0.41,
        "road_class_score": 0.61,
    }
    qc_features = {"role_count": 4, "avg_quality_score": 0.76}

    result = service.score(
        "pred-3",
        visual_features,
        geo_features,
        qc_features,
        0.08,
        [],
        _base_inputs("religious_gifts", confirmed=False, needs_confirmation=True),
    )

    assert result.shop_type_needs_confirmation is True
    assert result.shop_type_confirmed_by_user is False
    assert result.shop_type_source.endswith("blended_prior")
    assert any(flag.code == "shop_type_needs_confirmation" for flag in result.risk_flags)


def test_small_religious_store_stays_in_realistic_monthly_band():
    service = PredictionService()
    visual_features = {
        "inventory_depth_score": 0.42,
        "sku_diversity_score": 0.38,
        "storefront_visibility_score": 0.66,
        "merchandising_quality_score": 0.54,
        "refill_signal": 0.24,
        "visual_store_size_sqft_proxy": 130,
    }
    geo_features = {
        "footfall_proxy": 0.37,
        "catchment_density": 0.44,
        "competition_count_500m": 3,
        "commercial_mix": 0.28,
        "road_class_score": 0.54,
        "geo_source_confidence": 0.82,
    }
    qc_features = {"role_count": 4, "avg_quality_score": 0.79, "avg_blur_score": 0.22}

    result = service.score("pred-4", visual_features, geo_features, qc_features, 0.05, [], _base_inputs("religious_gifts"))

    assert result.monthly_revenue_range.min >= 30000
    assert result.monthly_revenue_range.max <= 180000
    assert result.monthly_income_range.max <= 45000
