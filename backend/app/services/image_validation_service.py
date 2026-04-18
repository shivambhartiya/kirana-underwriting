from app.schemas.upload import QualitySummary, UploadCompleteImage
from app.utils.enums import ImageRole
from app.utils.image_hash import duplicate_hint


class ImageValidationService:
    required_roles = {ImageRole.interior_shelf, ImageRole.counter, ImageRole.storefront}
    recommended_roles = {ImageRole.street_view}

    def validate_uploads(self, images: list[UploadCompleteImage]) -> QualitySummary:
        image_count_ok = 3 <= len(images) <= 5
        roles = {image.role for image in images}
        coverage_ok = len(roles) >= 3 and self.required_roles.issubset(roles)
        duplicate_warning = duplicate_hint([image.object_key for image in images])
        low_light_warning = any(
            (image.client_meta.brightness_score is not None and image.client_meta.brightness_score < 0.38)
            or (image.client_meta.width or 0) < 900
            for image in images
        )
        return QualitySummary(
            image_count_ok=image_count_ok,
            coverage_ok=coverage_ok,
            duplicate_warning=duplicate_warning,
            low_light_warning=low_light_warning,
        )
