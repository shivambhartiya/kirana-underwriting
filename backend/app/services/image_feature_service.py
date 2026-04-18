from app.models.image_metadata import ImageMetadata
from app.utils.geo_math import bounded_score, clamp


class ImageFeatureService:
    vision_model_version = "yolov8-kirana-v1"

    def extract_features(self, images: list[ImageMetadata]) -> tuple[dict, dict]:
        image_count = max(len(images), 1)
        quality_values = [float(image.quality_score or 0.68) for image in images]
        brightness_values = [float(image.brightness_score or 0.56) for image in images]
        blur_values = [float(image.blur_score or 0.22) for image in images]
        megapixel_scores = [
            clamp((((image.width or 0) * (image.height or 0)) / 1_250_000), 0.1, 1.0)
            for image in images
        ]

        resolution_score = bounded_score(*megapixel_scores)
        avg_quality = bounded_score(*quality_values)
        avg_brightness = bounded_score(*brightness_values)
        avg_blur = bounded_score(*blur_values)
        clarity_score = clamp((avg_quality * 0.58) + ((1 - avg_blur) * 0.24) + (resolution_score * 0.18), 0.15, 0.98)

        role_set = {image.role for image in images}
        storefront_present = "storefront" in role_set
        street_present = "street_view" in role_set
        counter_present = "counter" in role_set
        shelf_present = "interior_shelf" in role_set

        shelf_density = clamp(
            0.28
            + (0.18 if shelf_present else 0.0)
            + (0.08 * (image_count - 2))
            + (clarity_score * 0.18)
            - (avg_blur * 0.10),
            0.2,
            0.88,
        )
        sku_diversity = clamp(
            0.24
            + (0.06 * image_count)
            + (0.12 if shelf_present and counter_present else 0.0)
            + (clarity_score * 0.12),
            0.18,
            0.82,
        )
        inventory_depth = clamp(
            0.22
            + (shelf_density * 0.42)
            + (sku_diversity * 0.18)
            + (0.10 if shelf_present else 0.0)
            + (0.05 if counter_present else 0.0),
            0.2,
            0.84,
        )
        refill_signal = clamp(
            0.16
            + (clarity_score * 0.16)
            + (0.08 if counter_present else 0.0)
            + (0.05 if image_count >= 4 else 0.0),
            0.12,
            0.58,
        )
        storefront_visibility = clamp(
            0.22
            + (0.34 if storefront_present else 0.0)
            + (0.18 if street_present else 0.0)
            + (avg_brightness * 0.10)
            + (clarity_score * 0.12),
            0.18,
            0.95,
        )
        merchandising_quality = clamp(
            (clarity_score * 0.34) + (shelf_density * 0.28) + (sku_diversity * 0.18) + (avg_brightness * 0.20),
            0.2,
            0.92,
        )

        role_bonus = (22 if storefront_present else 0) + (14 if street_present else 0) + (12 if counter_present else 0) + (18 if shelf_present else 0)
        visual_store_size = round(90 + (image_count * 14) + role_bonus + (clarity_score * 46), 2)
        inventory_value_proxy = round((inventory_depth * visual_store_size * 420) + (sku_diversity * 18000), 2)

        visual_features = {
            "shelf_density_index": round(shelf_density, 3),
            "sku_diversity_score": round(sku_diversity, 3),
            "inventory_value_proxy": inventory_value_proxy,
            "inventory_depth_score": round(inventory_depth, 3),
            "refill_signal": round(refill_signal, 3),
            "storefront_visibility_score": round(storefront_visibility, 3),
            "merchandising_quality_score": round(merchandising_quality, 3),
            "visual_store_size_sqft_proxy": visual_store_size,
            "clarity_score": round(clarity_score, 3),
        }
        qc_features = {
            "image_count": len(images),
            "role_count": len(role_set),
            "duplicate_count": sum(1 for image in images if image.is_duplicate),
            "avg_quality_score": round(avg_quality, 3),
            "avg_brightness_score": round(avg_brightness, 3),
            "avg_blur_score": round(avg_blur, 3),
        }
        return visual_features, qc_features
