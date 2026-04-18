from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import DbSession, get_current_user
from app.core.object_store import create_presigned_upload
from app.models.audit_log import AuditLog
from app.models.image_metadata import ImageMetadata
from app.models.session import SessionRecord
from app.repos.audit_repo import AuditRepo
from app.repos.session_repo import SessionRepo
from app.schemas.upload import (
    UploadCompleteRequest,
    UploadCompleteResponse,
    UploadConstraints,
    UploadDescriptor,
    UploadInitRequest,
    UploadInitResponse,
    ImageRoleSuggestionRequest,
    ImageRoleSuggestionResponse,
    ShopTypeSuggestionRequest,
    ShopTypeSuggestionResponse,
)
from app.services.image_validation_service import ImageValidationService
from app.services.image_role_service import ImageRoleService
from app.services.shop_type_service import ShopTypeService
from app.utils.enums import ImageRole, SessionStatus


router = APIRouter()


@router.post("/sessions")
def create_session(db: DbSession, user=Depends(get_current_user)):
    repo = SessionRepo(db)
    session = repo.create(SessionRecord(user_id=user.id))
    AuditRepo(db).create(AuditLog(user_id=user.id, session_id=session.id, action="session_created", entity_type="session", entity_id=session.id))
    return {"session_id": session.id, "status": session.status}


@router.post("/upload-images/init", response_model=UploadInitResponse)
def init_uploads(payload: UploadInitRequest, db: DbSession, user=Depends(get_current_user)):
    repo = SessionRepo(db)
    session = repo.get(payload.session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    uploads = []
    for image in payload.images:
        object_key = f"sessions/{payload.session_id}/{image.role.value}/{image.filename}"
        uploads.append(
            UploadDescriptor(
                object_key=object_key,
                upload_url=create_presigned_upload(object_key, image.mime_type),
                role=image.role,
            )
        )
    return UploadInitResponse(
        session_id=payload.session_id,
        uploads=uploads,
        constraints=UploadConstraints(
            required_roles=[ImageRole.interior_shelf, ImageRole.counter, ImageRole.storefront],
            recommended_roles=[ImageRole.street_view],
        ),
    )


@router.post("/upload-images/complete", response_model=UploadCompleteResponse)
def complete_uploads(payload: UploadCompleteRequest, db: DbSession, user=Depends(get_current_user)):
    repo = SessionRepo(db)
    session = repo.get(payload.session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    quality_summary = ImageValidationService().validate_uploads(payload.images)
    for image in payload.images:
        db.add(
            ImageMetadata(
                session_id=payload.session_id,
                object_key=image.object_key,
                role=image.role.value,
                mime_type=image.mime_type,
                width=image.client_meta.width,
                height=image.client_meta.height,
                file_size_bytes=image.client_meta.file_size_bytes,
                quality_score=image.client_meta.quality_score or 0.72,
                blur_score=image.client_meta.blur_score or 0.24,
                brightness_score=image.client_meta.brightness_score or 0.58,
                phash=image.object_key[-16:],
                is_duplicate=quality_summary.duplicate_warning,
            )
        )
    session.status = SessionStatus.uploaded.value
    db.add(session)
    db.commit()
    AuditRepo(db).create(AuditLog(user_id=user.id, session_id=session.id, action="images_uploaded", entity_type="session", entity_id=session.id))
    return UploadCompleteResponse(
        session_id=payload.session_id,
        accepted=quality_summary.image_count_ok and quality_summary.coverage_ok,
        quality_summary=quality_summary,
        next_step="process_location",
    )


@router.post("/upload-images/suggest-roles", response_model=ImageRoleSuggestionResponse)
def suggest_roles(payload: ImageRoleSuggestionRequest, user=Depends(get_current_user)):
    return ImageRoleService().suggest_roles(payload.filenames, payload.image_hints)


@router.post("/upload-images/suggest-shop-type", response_model=ShopTypeSuggestionResponse)
def suggest_shop_type(payload: ShopTypeSuggestionRequest, user=Depends(get_current_user)):
    return ShopTypeService().suggest_shop_type(payload.filenames, payload.image_hints)
