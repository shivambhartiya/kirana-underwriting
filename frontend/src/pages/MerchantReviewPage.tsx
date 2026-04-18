import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";

import { createPrediction } from "../api/prediction";
import type { RootState } from "../app/store";
import { setOptionalInputs, setPredictionId } from "../app/store";
import { FlowProgress } from "../components/FlowProgress";

const prettifyLabel = (value: string) => (value === "religious_gifts" ? "Pooja + Gifts" : value.split("_").join(" "));

export function MerchantReviewPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const session = useSelector((state: RootState) => state.session);
  const shopTypeDetection = useSelector((state: RootState) => state.session.shopTypeDetection);
  const optionalVideo = useSelector((state: RootState) => state.session.optionalVideo);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit() {
    if (!session.sessionId) return;

    setIsSubmitting(true);
    setStatusMessage("Running underwriting. The system is blending image quality, location context, shop type, and business details into a range-based estimate.");
    setErrorMessage("");

    try {
      const response = await createPrediction({
        session_id: session.sessionId,
        optional_inputs: {
          shop_type: session.optionalInputs.shopType,
          shop_size_sqft: Number(session.optionalInputs.shopSizeSqft || 0),
          monthly_rent: Number(session.optionalInputs.monthlyRent || 0),
          years_in_operation: Number(session.optionalInputs.yearsInOperation || 0),
          video_duration_seconds: optionalVideo?.durationSeconds,
          shop_type_confidence: shopTypeDetection?.confidence,
          shop_type_source: shopTypeDetection?.source || "manual_or_default",
          shop_type_candidates: shopTypeDetection?.topCandidates.map((candidate) => ({
            shop_type: candidate.shopType,
            confidence: candidate.confidence,
            reasons: candidate.reasons,
          })),
          shop_type_needs_confirmation: shopTypeDetection?.needsConfirmation,
          shop_type_confirmed_by_user: session.optionalInputs.shopTypeConfirmedByUser,
        },
        consent: { credit_model_processing: true },
      });

      dispatch(setPredictionId(response.prediction_id));
      navigate(`/results/${response.prediction_id}`);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Underwriting failed.");
      setStatusMessage("");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="space-y-6">
      <FlowProgress current="review" />

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="panel p-8">
          <p className="text-sm uppercase tracking-[0.2em] text-pine">Review</p>
          <h2 className="mt-4 text-3xl font-semibold">Review the assumptions before underwriting</h2>

          <ul className="mt-6 space-y-3 text-ink/75">
            <li>Images captured: {session.images.length}</li>
            <li>Location set: {session.location?.formatted_address || "Yes"}</li>
            <li>Output format: daily sales range, monthly revenue range, normalized monthly income range, confidence score, and structured risk flags.</li>
          </ul>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <label className="text-sm">
              <span className="mb-2 block text-ink/65">Detected or selected shop type</span>
              <select
                className="input"
                value={session.optionalInputs.shopType}
                onChange={(event) =>
                  dispatch(
                    setOptionalInputs({
                      shopType: event.target.value,
                      shopTypeConfirmedByUser: shopTypeDetection?.needsConfirmation ? false : session.optionalInputs.shopTypeConfirmedByUser,
                    }),
                  )
                }
              >
                <option value="kirana_general">kirana general</option>
                <option value="vegetable_fruit">vegetable fruit</option>
                <option value="pharmacy_medical">medical or pharmacy</option>
                <option value="fast_food_qsr">fast food</option>
                <option value="religious_gifts">pooja + gifts</option>
                <option value="jewellery">jewellery</option>
                <option value="bakery_sweets">bakery or sweets</option>
                <option value="mobile_electronics">mobile or electronics</option>
                <option value="apparel_boutique">apparel or boutique</option>
              </select>
            </label>

            <label className="text-sm">
              <span className="mb-2 block text-ink/65">Shop size (sq ft)</span>
              <input
                className="input"
                value={session.optionalInputs.shopSizeSqft}
                onChange={(event) => dispatch(setOptionalInputs({ shopSizeSqft: event.target.value }))}
              />
            </label>

            <label className="text-sm">
              <span className="mb-2 block text-ink/65">Monthly rent (INR)</span>
              <input
                className="input"
                value={session.optionalInputs.monthlyRent}
                onChange={(event) => dispatch(setOptionalInputs({ monthlyRent: event.target.value }))}
              />
            </label>

            <label className="text-sm">
              <span className="mb-2 block text-ink/65">Years in operation</span>
              <input
                className="input"
                value={session.optionalInputs.yearsInOperation}
                onChange={(event) => dispatch(setOptionalInputs({ yearsInOperation: event.target.value }))}
              />
            </label>
          </div>

          <button
            className="button-primary mt-6 disabled:cursor-not-allowed disabled:opacity-60"
            onClick={handleSubmit}
            disabled={isSubmitting || Boolean(shopTypeDetection?.needsConfirmation && !session.optionalInputs.shopTypeConfirmedByUser)}
          >
            {isSubmitting ? "Running underwriting..." : "Run underwriting"}
          </button>

          {shopTypeDetection?.needsConfirmation && (
            <label className="mt-4 flex items-start gap-3 rounded-2xl bg-coral/8 px-4 py-3 text-sm text-ink/75">
              <input
                checked={session.optionalInputs.shopTypeConfirmedByUser}
                className="mt-1"
                type="checkbox"
                onChange={(event) => dispatch(setOptionalInputs({ shopTypeConfirmedByUser: event.target.checked }))}
              />
              <span>
                I confirm this store should be underwritten as <span className="font-semibold">{prettifyLabel(session.optionalInputs.shopType)}</span>.
              </span>
            </label>
          )}

          {statusMessage && (
            <div className="mt-4 rounded-2xl bg-pine/8 px-4 py-3 text-sm text-pine">
              <div className="flex items-center gap-3">
                {isSubmitting && <span className="h-4 w-4 animate-spin rounded-full border-2 border-pine/30 border-t-pine" />}
                <span>{statusMessage}</span>
              </div>
            </div>
          )}

          {errorMessage && <div className="mt-4 rounded-2xl bg-coral/10 px-4 py-3 text-sm text-coral">{errorMessage}</div>}
        </div>

        <div className="panel p-8">
          <p className="text-sm text-ink/70">
            These optional inputs directly influence the range width, margin assumptions, and confidence score. Better details make the underwriting output more grounded.
          </p>

          {shopTypeDetection && (
            <div className="mt-4 rounded-2xl bg-clay/30 px-4 py-3 text-sm text-ink/75">
              Auto-detected shop type: <span className="font-semibold">{prettifyLabel(shopTypeDetection.shopType)}</span> ({Math.round(shopTypeDetection.confidence * 100)}% confidence)
            </div>
          )}

          {shopTypeDetection?.needsConfirmation && (
            <div className="mt-4 rounded-2xl bg-coral/8 px-4 py-3 text-sm text-coral">
              This category is still provisional. Please choose the right shop type and confirm it before running underwriting.
            </div>
          )}

          {!!shopTypeDetection?.topCandidates.length && (
            <div className="mt-4 space-y-2 rounded-2xl bg-clay/20 px-4 py-4 text-sm text-ink/75">
              <p className="font-semibold text-ink">Top candidates</p>
              {shopTypeDetection.topCandidates.map((candidate) => (
                <div key={candidate.shopType}>
                  <span className="font-medium">{prettifyLabel(candidate.shopType)}</span> - {Math.round(candidate.confidence * 100)}%
                </div>
              ))}
            </div>
          )}

          {optionalVideo && (
            <div className="mt-4 rounded-2xl bg-clay/30 px-4 py-3 text-sm text-ink/75">
              Short video attached: {optionalVideo.fileName} - {optionalVideo.durationSeconds}s
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
