from pydantic import BaseModel, Field

from app.utils.enums import ImageRole, ShopType


class UploadImageRequest(BaseModel):
    filename: str
    mime_type: str
    role: ImageRole


class UploadInitRequest(BaseModel):
    session_id: str
    images: list[UploadImageRequest] = Field(min_length=1, max_length=5)


class UploadDescriptor(BaseModel):
    object_key: str
    upload_url: str
    role: ImageRole


class UploadConstraints(BaseModel):
    min_images: int = 3
    max_images: int = 5
    required_roles: list[ImageRole]
    recommended_roles: list[ImageRole]


class UploadInitResponse(BaseModel):
    session_id: str
    uploads: list[UploadDescriptor]
    constraints: UploadConstraints


class ClientMeta(BaseModel):
    width: int | None = None
    height: int | None = None
    file_size_bytes: int | None = None
    quality_score: float | None = None
    brightness_score: float | None = None
    blur_score: float | None = None


class UploadCompleteImage(BaseModel):
    object_key: str
    role: ImageRole
    mime_type: str = "image/jpeg"
    client_meta: ClientMeta = Field(default_factory=ClientMeta)


class UploadCompleteRequest(BaseModel):
    session_id: str
    images: list[UploadCompleteImage] = Field(min_length=1, max_length=5)


class QualitySummary(BaseModel):
    image_count_ok: bool
    coverage_ok: bool
    duplicate_warning: bool
    low_light_warning: bool


class UploadCompleteResponse(BaseModel):
    session_id: str
    accepted: bool
    quality_summary: QualitySummary
    next_step: str


class ImageRoleSuggestionRequest(BaseModel):
    filenames: list[str] = Field(min_length=1, max_length=5)
    image_hints: list[dict] = Field(default_factory=list)


class ImageRoleSuggestion(BaseModel):
    filename: str
    suggested_role: ImageRole
    confidence: float
    reason: str


class ImageRoleSuggestionResponse(BaseModel):
    suggestions: list[ImageRoleSuggestion]


class ShopTypeSuggestionRequest(BaseModel):
    filenames: list[str] = Field(min_length=1, max_length=5)
    image_hints: list[dict] = Field(default_factory=list)


class ShopTypeCandidate(BaseModel):
    shop_type: ShopType
    confidence: float
    reasons: list[str] = Field(default_factory=list)


class ShopTypeSuggestionResponse(BaseModel):
    detected_shop_type: ShopType
    confidence: float
    source: str
    reasoning: list[str] = Field(default_factory=list)
    top_candidates: list[ShopTypeCandidate] = Field(default_factory=list)
    needs_confirmation: bool = False
