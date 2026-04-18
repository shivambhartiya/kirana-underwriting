from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.shop_type_service import ShopTypeService


def test_pooja_style_hints_rank_religious_gifts_above_pharmacy():
    service = ShopTypeService()
    result = service.suggest_shop_type(
        filenames=["2026-03-21.jpg", "images.jpg"],
        image_hints=[
            {
                "brightness_score": 0.72,
                "texture_score": 0.44,
                "warm_ratio": 0.46,
                "green_ratio": 0.05,
                "saturation_score": 0.61,
                "edge_density": 0.24,
                "contrast_score": 0.53,
                "red_ratio": 0.28,
                "yellow_ratio": 0.22,
                "white_ratio": 0.18,
            },
            {
                "brightness_score": 0.69,
                "texture_score": 0.40,
                "warm_ratio": 0.43,
                "green_ratio": 0.06,
                "saturation_score": 0.58,
                "edge_density": 0.21,
                "contrast_score": 0.49,
                "red_ratio": 0.24,
                "yellow_ratio": 0.20,
                "white_ratio": 0.19,
            },
        ],
    )

    assert result.detected_shop_type.value == "religious_gifts"
    assert result.top_candidates[0].shop_type.value == "religious_gifts"
    assert all(candidate.shop_type.value != "pharmacy_medical" or index > 0 for index, candidate in enumerate(result.top_candidates))


def test_pharmacy_style_hints_still_rank_pharmacy_medical():
    service = ShopTypeService()
    result = service.suggest_shop_type(
        filenames=["chemist_front.jpg"],
        image_hints=[
            {
                "brightness_score": 0.84,
                "texture_score": 0.26,
                "warm_ratio": 0.08,
                "green_ratio": 0.24,
                "saturation_score": 0.20,
                "edge_density": 0.14,
                "contrast_score": 0.24,
                "red_ratio": 0.05,
                "yellow_ratio": 0.04,
                "white_ratio": 0.42,
            }
        ],
    )

    assert result.detected_shop_type.value == "pharmacy_medical"
