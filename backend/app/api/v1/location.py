from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import DbSession, get_current_user
from app.models.audit_log import AuditLog
from app.repos.audit_repo import AuditRepo
from app.repos.session_repo import SessionRepo
from app.schemas.location import LocationProcessRequest, LocationProcessResponse, LocationSuggestionResponse, ReverseGeocodeResponse
from app.services.geo_service import GeoService
from app.utils.enums import SessionStatus


router = APIRouter()


@router.get("/location-suggest", response_model=LocationSuggestionResponse)
def suggest_location(query: str, bias_lat: float | None = None, bias_lng: float | None = None, user=Depends(get_current_user)):
    return GeoService().suggest_addresses(query, bias_lat=bias_lat, bias_lng=bias_lng)


@router.get("/reverse-geocode", response_model=ReverseGeocodeResponse)
def reverse_geocode(lat: float, lng: float, user=Depends(get_current_user)):
    return GeoService().reverse_geocode(lat, lng)


@router.post("/process-location", response_model=LocationProcessResponse)
def process_location(payload: LocationProcessRequest, db: DbSession, user=Depends(get_current_user)):
    repo = SessionRepo(db)
    session = repo.get(payload.session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if not payload.gps and not payload.manual_address and not payload.manual_selection:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GPS or manual address is required")

    geo_service = GeoService()
    if payload.gps:
        lat, lng = payload.gps.lat, payload.gps.lng
        source = "gps_reverse_geocode"
    elif payload.manual_selection:
        lat, lng = payload.manual_selection.lat, payload.manual_selection.lng
        source = "manual_selection"
    else:
        try:
            lat, lng = geo_service.geocode_address(payload.manual_address or "", bias_lat=(payload.gps.lat if payload.gps else None), bias_lng=(payload.gps.lng if payload.gps else None))
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
        source = "manual_address_geocode"

    normalized, serviceability, preview, _ = geo_service.normalize_location(lat, lng, source)
    if payload.formatted_address_override:
        normalized.formatted_address = payload.formatted_address_override
    session.gps_lat = normalized.lat
    session.gps_lng = normalized.lng
    session.normalized_address = normalized.formatted_address
    session.location_source = normalized.source
    session.status = SessionStatus.located.value
    repo.save(session)
    AuditRepo(db).create(AuditLog(user_id=user.id, session_id=session.id, action="location_processed", entity_type="session", entity_id=session.id))
    return LocationProcessResponse(
        session_id=payload.session_id,
        normalized_location=normalized,
        serviceability=serviceability,
        geo_preview=preview,
    )
