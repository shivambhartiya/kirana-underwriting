from hashlib import md5

import httpx

from app.core.config import get_settings
from app.schemas.location import GeoPreview, LocationSuggestionItem, LocationSuggestionResponse, NormalizedLocation, ReverseGeocodeResponse, Serviceability
from app.utils.geo_math import clamp, haversine_km


class GeoService:
    geo_model_version = "geo-features-v2-live-context"
    settings = get_settings()

    def _seed(self, lat: float, lng: float) -> int:
        digest = md5(f"{lat:.5f}:{lng:.5f}".encode("utf-8")).hexdigest()
        return int(digest[:8], 16)

    def _token_overlap(self, query: str, label: str) -> float:
        query_tokens = {token for token in query.lower().split() if token}
        label_tokens = {token for token in label.lower().replace(",", " ").split() if token}
        if not query_tokens:
            return 0.0
        return len(query_tokens & label_tokens) / len(query_tokens)

    def _fake_geocode(self, manual_address: str) -> tuple[float, float]:
        digest = md5(manual_address.strip().lower().encode("utf-8")).hexdigest()
        lat = 19.0 + (int(digest[:4], 16) % 700) / 1000
        lng = 72.8 + (int(digest[4:8], 16) % 700) / 1000
        return round(lat, 6), round(lng, 6)

    def _rank_suggestions(
        self,
        query: str,
        suggestions: list[LocationSuggestionItem],
        bias_lat: float | None = None,
        bias_lng: float | None = None,
    ) -> list[LocationSuggestionItem]:
        ranked: list[tuple[float, LocationSuggestionItem]] = []
        for item in suggestions:
            source_weight = 0.12 if item.source.startswith("google") else 0.06
            overlap_score = self._token_overlap(query, item.label) * 0.58
            distance_penalty = 0.0
            if bias_lat is not None and bias_lng is not None:
                distance_km = haversine_km(bias_lat, bias_lng, item.lat, item.lng)
                distance_penalty = clamp(distance_km / 25, 0.0, 0.36)
            ranked.append((source_weight + overlap_score - distance_penalty, item))
        ranked.sort(key=lambda value: value[0], reverse=True)
        return [item for _, item in ranked[:5]]

    def _google_autocomplete(self, query: str, bias_lat: float | None = None, bias_lng: float | None = None) -> list[LocationSuggestionItem]:
        if not self.settings.google_maps_api_key:
            return []

        params = {
            "input": query,
            "components": "country:in",
            "key": self.settings.google_maps_api_key,
        }
        if bias_lat is not None and bias_lng is not None:
            params["locationbias"] = f"circle:5000@{bias_lat},{bias_lng}"

        response = httpx.get(
            "https://maps.googleapis.com/maps/api/place/autocomplete/json",
            params=params,
            timeout=5.0,
        )
        payload = response.json()
        predictions = payload.get("predictions", [])[:5]
        suggestions: list[LocationSuggestionItem] = []

        for prediction in predictions:
            details = httpx.get(
                "https://maps.googleapis.com/maps/api/place/details/json",
                params={
                    "place_id": prediction["place_id"],
                    "fields": "geometry/location,formatted_address",
                    "key": self.settings.google_maps_api_key,
                },
                timeout=5.0,
            ).json()
            result = details.get("result") or {}
            location = ((result.get("geometry") or {}).get("location")) or {}
            if "lat" in location and "lng" in location:
                suggestions.append(
                    LocationSuggestionItem(
                        label=result.get("formatted_address", prediction.get("description", query)),
                        lat=float(location["lat"]),
                        lng=float(location["lng"]),
                        source="google_places",
                    )
                )
        return suggestions

    def _nominatim_search(self, query: str) -> list[LocationSuggestionItem]:
        response = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query,
                "format": "jsonv2",
                "limit": 6,
                "countrycodes": "in",
                "addressdetails": 1,
                "namedetails": 1,
                "dedupe": 1,
            },
            headers={"User-Agent": "kirana-underwriting-app"},
            timeout=6.0,
        )
        payload = response.json()
        return [
            LocationSuggestionItem(
                label=item.get("display_name", query),
                lat=float(item["lat"]),
                lng=float(item["lon"]),
                source="nominatim",
            )
            for item in payload[:6]
            if "lat" in item and "lon" in item
        ]

    def geocode_address(self, manual_address: str, bias_lat: float | None = None, bias_lng: float | None = None) -> tuple[float, float]:
        suggestions = self.suggest_addresses(manual_address, bias_lat=bias_lat, bias_lng=bias_lng).suggestions
        if suggestions:
            return suggestions[0].lat, suggestions[0].lng
        if self.settings.enable_fake_geo:
            return self._fake_geocode(manual_address)
        raise ValueError("Unable to resolve that address accurately. Please pick a suggestion or use the map pin.")

    def suggest_addresses(self, query: str, bias_lat: float | None = None, bias_lng: float | None = None) -> LocationSuggestionResponse:
        if len(query.strip()) < 3:
            return LocationSuggestionResponse(suggestions=[])

        suggestions: list[LocationSuggestionItem] = []
        try:
            suggestions.extend(self._google_autocomplete(query, bias_lat=bias_lat, bias_lng=bias_lng))
        except Exception:
            pass
        try:
            suggestions.extend(self._nominatim_search(query))
        except Exception:
            pass

        deduped: list[LocationSuggestionItem] = []
        seen = set()
        for item in suggestions:
            key = (round(item.lat, 5), round(item.lng, 5), item.label.lower())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)

        if deduped:
            return LocationSuggestionResponse(suggestions=self._rank_suggestions(query, deduped, bias_lat=bias_lat, bias_lng=bias_lng))
        if self.settings.enable_fake_geo:
            base_lat, base_lng = self._fake_geocode(query)
            return LocationSuggestionResponse(
                suggestions=[
                    LocationSuggestionItem(
                        label=f"{query.title()}, India",
                        lat=base_lat,
                        lng=base_lng,
                        source="fallback",
                    )
                ]
            )
        return LocationSuggestionResponse(suggestions=[])

    def reverse_geocode(self, lat: float, lng: float) -> ReverseGeocodeResponse:
        if self.settings.google_maps_api_key:
            try:
                response = httpx.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params={"latlng": f"{lat},{lng}", "key": self.settings.google_maps_api_key, "result_type": "street_address|premise|route|sublocality"},
                    timeout=5.0,
                )
                payload = response.json()
                if payload.get("results"):
                    return ReverseGeocodeResponse(
                        label=payload["results"][0].get("formatted_address", f"Lat {lat:.5f}, Lng {lng:.5f}"),
                        lat=lat,
                        lng=lng,
                        source="google_reverse",
                    )
            except Exception:
                pass

        try:
            response = httpx.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={"lat": lat, "lon": lng, "format": "jsonv2", "zoom": 18, "addressdetails": 1},
                headers={"User-Agent": "kirana-underwriting-app"},
                timeout=6.0,
            )
            payload = response.json()
            return ReverseGeocodeResponse(
                label=payload.get("display_name", f"Lat {lat:.5f}, Lng {lng:.5f}"),
                lat=lat,
                lng=lng,
                source="nominatim_reverse",
            )
        except Exception:
            return ReverseGeocodeResponse(
                label=f"Approx. location at {lat:.5f}, {lng:.5f}",
                lat=lat,
                lng=lng,
                source="fallback_reverse",
            )

    def _overpass_context(self, lat: float, lng: float) -> dict:
        overpass_query = f"""
[out:json][timeout:8];
(
  node(around:500,{lat},{lng})[shop];
  way(around:500,{lat},{lng})[shop];
  node(around:500,{lat},{lng})[amenity];
  way(around:500,{lat},{lng})[amenity];
  node(around:500,{lat},{lng})[highway=bus_stop];
  node(around:500,{lat},{lng})[public_transport];
  way(around:500,{lat},{lng})[highway];
);
out tags center qt;
""".strip()
        response = httpx.post(
            "https://overpass-api.de/api/interpreter",
            content=overpass_query,
            headers={"Content-Type": "text/plain"},
            timeout=9.0,
        )
        response.raise_for_status()
        payload = response.json()
        return payload

    def _context_from_live_sources(self, lat: float, lng: float) -> tuple[GeoPreview, dict]:
        payload = self._overpass_context(lat, lng)
        elements = payload.get("elements", [])
        shop_tags = []
        amenity_tags = []
        road_tags = []
        transport_hits = 0
        competition_hits = 0

        grocery_like = {"supermarket", "convenience", "greengrocer", "grocery", "department_store", "kiosk"}
        for element in elements:
            tags = element.get("tags") or {}
            shop = tags.get("shop")
            amenity = tags.get("amenity")
            highway = tags.get("highway")
            public_transport = tags.get("public_transport")

            if shop:
                shop_tags.append(shop)
                if shop in grocery_like:
                    competition_hits += 1
            if amenity:
                amenity_tags.append(amenity)
            if highway:
                road_tags.append(highway)
                if highway == "bus_stop":
                    transport_hits += 1
            if public_transport:
                transport_hits += 1

        poi_count = len(shop_tags) + len(amenity_tags) + transport_hits
        commercial_count = len(shop_tags) + sum(1 for amenity in amenity_tags if amenity in {"restaurant", "bank", "school", "hospital", "pharmacy", "marketplace", "cafe"})

        road_weights = {
            "residential": 0.35,
            "service": 0.3,
            "tertiary": 0.5,
            "secondary": 0.68,
            "primary": 0.84,
            "trunk": 0.9,
        }
        road_score = max((road_weights.get(road, 0.4) for road in road_tags), default=0.5)
        if road_score >= 0.8:
            road_class = "arterial"
        elif road_score >= 0.56:
            road_class = "secondary"
        else:
            road_class = "internal"

        footfall_proxy = clamp((road_score * 0.38) + (min(poi_count, 40) / 40 * 0.28) + (min(transport_hits, 6) / 6 * 0.16) + (min(commercial_count, 22) / 22 * 0.18), 0.14, 0.92)
        catchment_density = clamp(0.22 + (min(poi_count, 45) / 45 * 0.45) + (road_score * 0.18), 0.2, 0.9)
        commercial_mix = clamp(min(commercial_count, max(poi_count, 1)) / max(poi_count, 1), 0.12, 0.9)
        competition_density = round((competition_hits * 1.0) + (min(competition_hits + 2, 10) * 0.6) + (min(competition_hits + 4, 16) * 0.3), 2)

        preview = GeoPreview(
            road_class=road_class,
            poi_count_500m=poi_count,
            competition_count_500m=competition_hits,
            footfall_proxy=round(footfall_proxy, 2),
        )
        geo_features = {
            "catchment_density": round(catchment_density, 2),
            "footfall_proxy": round(footfall_proxy, 2),
            "competition_density": competition_density,
            "commercial_mix": round(commercial_mix, 2),
            "road_class_score": round(road_score, 2),
            "poi_count_500m": poi_count,
            "competition_count_500m": competition_hits,
            "geo_source_confidence": 0.86,
        }
        return preview, geo_features

    def _fallback_context(self, lat: float, lng: float) -> tuple[GeoPreview, dict]:
        seed = self._seed(lat, lng)
        road_class = ["internal", "secondary", "arterial"][seed % 3]
        road_class_score = {"internal": 0.35, "secondary": 0.62, "arterial": 0.82}[road_class]
        poi_count = 8 + (seed % 12)
        competition = 2 + (seed % 5)
        footfall_proxy = clamp(0.28 + (road_class_score * 0.35) + (poi_count / 40 * 0.18) - (competition / 20 * 0.05), 0.18, 0.72)
        catchment_density = clamp(0.26 + (poi_count / 45 * 0.22) + (road_class_score * 0.12), 0.22, 0.68)
        commercial_mix = clamp(0.24 + (competition / 20 * 0.20) + (road_class_score * 0.10), 0.18, 0.56)

        preview = GeoPreview(
            road_class=road_class,
            poi_count_500m=poi_count,
            competition_count_500m=competition,
            footfall_proxy=round(footfall_proxy, 2),
        )
        geo_features = {
            "catchment_density": round(catchment_density, 2),
            "footfall_proxy": round(footfall_proxy, 2),
            "competition_density": round((competition * 1.0) + ((competition + 1) * 0.6) + ((competition + 3) * 0.3), 2),
            "commercial_mix": round(commercial_mix, 2),
            "road_class_score": road_class_score,
            "poi_count_500m": poi_count,
            "competition_count_500m": competition,
            "geo_source_confidence": 0.48,
        }
        return preview, geo_features

    def normalize_location(self, lat: float, lng: float, source: str) -> tuple[NormalizedLocation, Serviceability, GeoPreview, dict]:
        reverse = self.reverse_geocode(lat, lng)
        normalized = NormalizedLocation(lat=lat, lng=lng, formatted_address=reverse.label, source=source)
        serviceability = Serviceability(eligible_area=True, reason=None)

        try:
            preview, geo_features = self._context_from_live_sources(lat, lng)
        except Exception:
            preview, geo_features = self._fallback_context(lat, lng)

        return normalized, serviceability, preview, geo_features
