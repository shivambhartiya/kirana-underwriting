import { api } from "./client";

export function processLocation(payload: unknown) {
  return api("/process-location", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function suggestLocations(query: string, bias?: { lat: number; lng: number } | null) {
  const encoded = encodeURIComponent(query);
  const biasQuery = bias ? `&bias_lat=${encodeURIComponent(String(bias.lat))}&bias_lng=${encodeURIComponent(String(bias.lng))}` : "";
  return api<{ suggestions: { label: string; lat: number; lng: number; source: string }[] }>(`/location-suggest?query=${encoded}${biasQuery}`, {
    method: "GET",
  });
}

export function reverseGeocode(lat: number, lng: number) {
  return api<{ label: string; lat: number; lng: number; source: string }>(`/reverse-geocode?lat=${lat}&lng=${lng}`, {
    method: "GET",
  });
}
