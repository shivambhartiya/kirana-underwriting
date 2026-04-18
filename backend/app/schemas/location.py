from pydantic import BaseModel, Field


class GPSInput(BaseModel):
    lat: float
    lng: float
    accuracy_meters: float | None = None


class LocationProcessRequest(BaseModel):
    session_id: str
    gps: GPSInput | None = None
    manual_address: str | None = None
    manual_selection: GPSInput | None = None
    formatted_address_override: str | None = None


class NormalizedLocation(BaseModel):
    lat: float
    lng: float
    formatted_address: str
    source: str


class Serviceability(BaseModel):
    eligible_area: bool
    reason: str | None = None


class GeoPreview(BaseModel):
    road_class: str
    poi_count_500m: int
    competition_count_500m: int
    footfall_proxy: float | None = None


class LocationProcessResponse(BaseModel):
    session_id: str
    normalized_location: NormalizedLocation
    serviceability: Serviceability
    geo_preview: GeoPreview


class LocationSuggestionItem(BaseModel):
    label: str
    lat: float
    lng: float
    source: str


class LocationSuggestionResponse(BaseModel):
    suggestions: list[LocationSuggestionItem]


class ReverseGeocodeResponse(BaseModel):
    label: str
    lat: float
    lng: float
    source: str
