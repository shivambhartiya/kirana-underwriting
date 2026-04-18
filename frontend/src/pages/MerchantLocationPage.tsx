import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";

import { processLocation, reverseGeocode, suggestLocations } from "../api/location";
import type { RootState } from "../app/store";
import { setLocation } from "../app/store";
import { FlowProgress } from "../components/FlowProgress";
import { MapPreview } from "../components/MapPreview";

type Suggestion = {
  label: string;
  lat: number;
  lng: number;
  source: string;
};

type PreviewLocation = {
  lat: number;
  lng: number;
  label: string;
  source: "gps" | "manual_selection";
  accuracyMeters?: number | null;
};

export function MerchantLocationPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const sessionId = useSelector((state: RootState) => state.session.sessionId);

  const [address, setAddress] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isResolvingPreview, setIsResolvingPreview] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [preview, setPreview] = useState<PreviewLocation | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    const handle = window.setTimeout(async () => {
      if (address.trim().length < 3) {
        setSuggestions([]);
        return;
      }
      try {
        setIsSearching(true);
        const response = await suggestLocations(address, preview ? { lat: preview.lat, lng: preview.lng } : null);
        setSuggestions(response.suggestions);
      } catch {
        setSuggestions([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => window.clearTimeout(handle);
  }, [address, preview]);

  function applyPreview(nextPreview: PreviewLocation) {
    setPreview(nextPreview);
    setAddress(nextPreview.label);
    setErrorMessage("");
  }

  async function handleGps() {
    if (!navigator.geolocation) {
      setErrorMessage("This browser does not support GPS location.");
      return;
    }

    setIsResolvingPreview(true);
    setErrorMessage("");
    setStatusMessage("Fetching your current GPS with high accuracy...");

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const response = await reverseGeocode(position.coords.latitude, position.coords.longitude);
          applyPreview({
            lat: response.lat,
            lng: response.lng,
            label: response.label,
            source: "gps",
            accuracyMeters: position.coords.accuracy,
          });
          setStatusMessage("GPS found. Please confirm the pin is on the exact storefront location.");
        } catch (error) {
          setErrorMessage(error instanceof Error ? error.message : "GPS lookup failed.");
          setStatusMessage("");
        } finally {
          setIsResolvingPreview(false);
        }
      },
      (error) => {
        setErrorMessage(error.message || "Unable to fetch your current GPS location.");
        setStatusMessage("");
        setIsResolvingPreview(false);
      },
      {
        enableHighAccuracy: true,
        maximumAge: 0,
        timeout: 12000,
      },
    );
  }

  async function handleUseTopSuggestion() {
    if (!address.trim()) return;
    setIsResolvingPreview(true);
    setErrorMessage("");
    setStatusMessage("Searching the address and placing the pin on the best match...");

    try {
      const response = await suggestLocations(address, preview ? { lat: preview.lat, lng: preview.lng } : null);
      const topSuggestion = response.suggestions[0];
      if (!topSuggestion) {
        throw new Error("No matching address was found. Please try a more specific shop or landmark.");
      }
      applyPreview({
        lat: topSuggestion.lat,
        lng: topSuggestion.lng,
        label: topSuggestion.label,
        source: "manual_selection",
        accuracyMeters: null,
      });
      setSuggestions(response.suggestions);
      setStatusMessage("Address match found. Drag the pin if needed, then confirm and continue.");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Address lookup failed.");
      setStatusMessage("");
    } finally {
      setIsResolvingPreview(false);
    }
  }

  async function handleMapPositionChange(lat: number, lng: number) {
    setIsResolvingPreview(true);
    setStatusMessage("Updating the location from the map pin...");

    try {
      const response = await reverseGeocode(lat, lng);
      applyPreview({
        lat: response.lat,
        lng: response.lng,
        label: response.label,
        source: "manual_selection",
        accuracyMeters: null,
      });
      setStatusMessage("Pin updated. Confirm and continue when the storefront marker looks right.");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to update the map location.");
      setStatusMessage("");
    } finally {
      setIsResolvingPreview(false);
    }
  }

  async function handleConfirmLocation() {
    if (!sessionId || !preview) return;

    setIsSubmitting(true);
    setErrorMessage("");
    setStatusMessage("Confirming the selected location and preparing geo features...");

    try {
      const response: any = await processLocation({
        session_id: sessionId,
        gps: preview.source === "gps" ? { lat: preview.lat, lng: preview.lng, accuracy_meters: preview.accuracyMeters ?? undefined } : null,
        manual_selection: { lat: preview.lat, lng: preview.lng },
        manual_address: address || preview.label,
        formatted_address_override: preview.label,
      });

      dispatch(setLocation(response.normalized_location));
      setStatusMessage("Location confirmed. Moving to underwriting review...");
      navigate("/merchant/review");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Location confirmation failed.");
      setStatusMessage("");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="space-y-6">
      <FlowProgress current="location" />

      <div className="grid gap-6 md:grid-cols-2">
        <div className="panel p-8">
          <p className="text-sm uppercase tracking-[0.2em] text-pine">Location</p>
          <h2 className="mt-4 text-3xl font-semibold">Confirm the exact shop pin before underwriting</h2>
          <p className="mt-3 text-sm text-ink/70">
            GPS is best when you are standing near the store. Manual search works too, but please choose a suggestion or adjust the map pin so the storefront and street context are accurate.
          </p>

          <div className="mt-6 space-y-4">
            <button className="button-primary" onClick={handleGps} disabled={isSubmitting || isResolvingPreview}>
              {isResolvingPreview ? "Locating..." : "Use current GPS"}
            </button>

            <div className="space-y-3">
              <input
                className="input"
                value={address}
                onChange={(event) => setAddress(event.target.value)}
                placeholder="Search shop address, locality, or nearby landmark"
              />
              {isSearching && <p className="text-xs text-ink/55">Searching precise matches near your current pin...</p>}
              <button className="button-secondary" onClick={handleUseTopSuggestion} disabled={!address.trim() || isSubmitting || isResolvingPreview}>
                Search address on map
              </button>
            </div>

            {!!suggestions.length && (
              <div className="rounded-3xl border border-ink/10 bg-white">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={`${suggestion.label}-${index}`}
                    className="block w-full border-b border-ink/5 px-4 py-3 text-left text-sm last:border-b-0 hover:bg-ink/5"
                    onClick={() =>
                      applyPreview({
                        lat: suggestion.lat,
                        lng: suggestion.lng,
                        label: suggestion.label,
                        source: "manual_selection",
                      })
                    }
                  >
                    <div className="font-medium text-ink">{suggestion.label}</div>
                    <div className="mt-1 text-xs text-ink/55">Source: {suggestion.source}</div>
                  </button>
                ))}
              </div>
            )}

            <button className="button-primary" onClick={handleConfirmLocation} disabled={!preview || isSubmitting || isResolvingPreview}>
              {isSubmitting ? "Confirming..." : "Confirm location and continue"}
            </button>

            {statusMessage && (
              <div className="rounded-2xl bg-pine/8 px-4 py-3 text-sm text-pine">
                <div className="flex items-center gap-3">
                  {(isSubmitting || isResolvingPreview) && <span className="h-4 w-4 animate-spin rounded-full border-2 border-pine/30 border-t-pine" />}
                  <span>{statusMessage}</span>
                </div>
              </div>
            )}

            {errorMessage && <div className="rounded-2xl bg-coral/10 px-4 py-3 text-sm text-coral">{errorMessage}</div>}
          </div>
        </div>

        <div className="panel p-8">
          <p className="text-sm text-ink/70">This map is interactive and now biases search around your selected area. Click anywhere or drag the pin to land on the exact storefront before you continue.</p>
          <div className="mt-4 rounded-2xl bg-clay/30 px-4 py-3 text-sm text-ink/75">
            Accuracy note: GPS uses high-accuracy browser location, manual search prefers live address matches near your current pin, and the blue radius shows how precise the device GPS is.
          </div>
          {preview && (
            <div className="mt-4 rounded-2xl bg-white px-4 py-3 text-sm text-ink/75 shadow-sm ring-1 ring-ink/8">
              <div className="font-medium text-ink">{preview.label}</div>
              <div className="mt-1 flex flex-wrap gap-4 text-xs text-ink/55">
                <span>Source: {preview.source === "gps" ? "device GPS" : "map selection"}</span>
                {preview.accuracyMeters ? <span>Estimated accuracy: ~{Math.round(preview.accuracyMeters)}m</span> : null}
              </div>
            </div>
          )}
          <div className="mt-6">
            <MapPreview
              lat={preview?.lat}
              lng={preview?.lng}
              label={preview?.label}
              accuracyMeters={preview?.accuracyMeters}
              locationSource={preview?.source === "gps" ? "device GPS" : preview?.source ? "manual search / pin" : undefined}
              onPositionChange={handleMapPositionChange}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
