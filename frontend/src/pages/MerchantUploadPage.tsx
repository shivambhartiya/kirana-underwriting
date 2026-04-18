import { useState, type ChangeEvent } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";

import { completeUploads, initUploads, performDirectUploads, suggestImageRoles, suggestShopType } from "../api/uploads";
import type { RootState } from "../app/store";
import { markUploaded, setImages, setOptionalVideo, setShopTypeDetection } from "../app/store";
import { FlowProgress } from "../components/FlowProgress";
import { MultiImageDropzone } from "../components/MultiImageDropzone";
import { analyzeImageFiles, type ImageHint } from "../utils/imageAnalysis";

const prettifyLabel = (value: string) => (value === "religious_gifts" ? "Pooja + Gifts" : value.split("_").join(" "));

export function MerchantUploadPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const sessionId = useSelector((state: RootState) => state.session.sessionId);
  const images = useSelector((state: RootState) => state.session.images);
  const shopTypeDetection = useSelector((state: RootState) => state.session.shopTypeDetection);
  const optionalVideo = useSelector((state: RootState) => state.session.optionalVideo);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [suggestions, setSuggestions] = useState<{ filename: string; suggested_role: string; confidence: number; reason: string }[]>([]);
  const [imageHints, setImageHints] = useState<ImageHint[]>([]);

  async function handleAutoAssign() {
    if (!images.length) return;
    setIsAnalyzing(true);
    setErrorMessage("");
    setStatusMessage("Analyzing image content to suggest roles and estimate the shop category...");
    try {
      const imageHints = await analyzeImageFiles(images.map((item) => item.file));
      setImageHints(imageHints);
      const response = await suggestImageRoles(images.map((item) => item.file.name), imageHints);
      const shopType = await suggestShopType(images.map((item) => item.file.name), imageHints);
      setSuggestions(response.suggestions);
      dispatch(
        setShopTypeDetection({
          shopType: shopType.detected_shop_type,
          confidence: shopType.confidence,
          source: shopType.source,
          reasoning: shopType.reasoning,
          topCandidates: shopType.top_candidates.map((candidate) => ({
            shopType: candidate.shop_type,
            confidence: candidate.confidence,
            reasons: candidate.reasons,
          })),
          needsConfirmation: shopType.needs_confirmation,
        }),
      );
      dispatch(
        setImages(
          images.map((item) => {
            const suggestion = response.suggestions.find((candidate) => candidate.filename === item.file.name);
            return suggestion ? { ...item, role: suggestion.suggested_role } : item;
          }),
        ),
      );
      setStatusMessage(
        shopType.needs_confirmation
          ? "Suggested image roles have been applied. Shop type needs confirmation before underwriting."
          : "Suggested image roles and shop type have been applied. Please quickly confirm them before continuing.",
      );
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Image analysis failed.");
      setStatusMessage("");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleVideo(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    const durationSeconds = await new Promise<number>((resolve) => {
      const video = document.createElement("video");
      const objectUrl = URL.createObjectURL(file);
      video.preload = "metadata";
      video.onloadedmetadata = () => {
        resolve(Number(video.duration.toFixed(2)));
        URL.revokeObjectURL(objectUrl);
      };
      video.src = objectUrl;
    });

    dispatch(setOptionalVideo({ fileName: file.name, durationSeconds }));
  }

  async function handleContinue() {
    if (!sessionId) return;
    setIsSubmitting(true);
    setErrorMessage("");

    try {
      const hints = imageHints.length === images.length ? imageHints : await analyzeImageFiles(images.map((item) => item.file));
      setImageHints(hints);
      setStatusMessage("Preparing secure uploads...");
      const descriptors = await initUploads({
        session_id: sessionId,
        images: images.map((item) => ({
          filename: item.file.name,
          mime_type: item.file.type || "image/jpeg",
          role: item.role,
        })),
      });

      setStatusMessage("Uploading images and validating coverage...");
      await performDirectUploads(descriptors.uploads, images.map((item) => item.file));
      await completeUploads({
        session_id: sessionId,
        images: descriptors.uploads.map((upload, index) => ({
          object_key: upload.object_key,
          role: upload.role,
          mime_type: images[index].file.type || "image/jpeg",
          client_meta: {
            width: hints[index]?.width || 1280,
            height: hints[index]?.height || 960,
            file_size_bytes: images[index].file.size,
            quality_score: Number(
              (
                ((hints[index]?.contrast_score || 0.45) * 0.32)
                + ((1 - Math.min(hints[index]?.edge_density || 0.25, 0.9)) * 0.08)
                + ((hints[index]?.brightness_score || 0.55) * 0.24)
                + ((hints[index]?.texture_score || 0.45) * 0.22)
                + ((hints[index]?.saturation_score || 0.38) * 0.14)
              ).toFixed(3),
            ),
            brightness_score: hints[index]?.brightness_score,
            blur_score: Number((1 - Math.min(hints[index]?.edge_density || 0.2, 0.95)).toFixed(3)),
          },
        })),
      });

      dispatch(markUploaded(true));
      setStatusMessage("Images accepted. Moving to the location confirmation step...");
      navigate("/merchant/location");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Upload failed.");
      setStatusMessage("");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="space-y-6">
      <FlowProgress current="images" />
      <MultiImageDropzone files={images} suggestions={suggestions} onChange={(nextFiles) => dispatch(setImages(nextFiles))} />

      <div className="panel p-6">
        <p className="text-sm text-ink/70">
          Upload 3 to 5 images. Include at least one storefront image, one counter image, and one interior shelf image. A street-context image improves location quality and confidence.
        </p>

        <div className="mt-4 flex flex-wrap gap-3">
          <button className="button-secondary" onClick={handleAutoAssign} disabled={!images.length || isSubmitting || isAnalyzing}>
            {isAnalyzing ? "Analyzing images..." : "Auto-detect image roles"}
          </button>
          <button className="button-primary" onClick={handleContinue} disabled={images.length < 3 || isSubmitting || isAnalyzing}>
            {isSubmitting ? "Uploading..." : "Continue to location"}
          </button>
        </div>

        {statusMessage && (
          <div className="mt-4 rounded-2xl bg-pine/8 px-4 py-3 text-sm text-pine">
            <div className="flex items-center gap-3">
              {(isSubmitting || isAnalyzing) && <span className="h-4 w-4 animate-spin rounded-full border-2 border-pine/30 border-t-pine" />}
              <span>{statusMessage}</span>
            </div>
          </div>
        )}

        {errorMessage && <div className="mt-4 rounded-2xl bg-coral/10 px-4 py-3 text-sm text-coral">{errorMessage}</div>}

        {!!suggestions.length && (
          <div className="mt-4 rounded-2xl bg-clay/30 px-4 py-3 text-sm text-ink/75">
            The app suggested image roles automatically. Please confirm storefront, counter, and street-view assignments before moving on.
          </div>
        )}

        <div className="mt-4 rounded-2xl border border-ink/10 bg-white px-4 py-4">
          <p className="text-sm font-semibold text-ink">Optional short video (5 to 10 seconds)</p>
          <p className="mt-1 text-sm text-ink/60">A short pan of the store helps improve confidence and makes the underwriting range less brittle.</p>
          <input className="mt-3" type="file" accept="video/*" onChange={handleVideo} />
          {optionalVideo && <p className="mt-2 text-sm text-pine">Attached: {optionalVideo.fileName} - {optionalVideo.durationSeconds}s</p>}
        </div>

        {shopTypeDetection && (
          <div className="mt-4 rounded-2xl border border-ink/10 bg-white px-4 py-4">
            <p className="text-sm font-semibold text-ink">Detected shop type</p>
            <p className="mt-2 text-lg font-semibold text-pine">{prettifyLabel(shopTypeDetection.shopType)}</p>
            <p className="mt-1 text-sm text-ink/60">Confidence {Math.round(shopTypeDetection.confidence * 100)}% - {shopTypeDetection.source}</p>
            {!!shopTypeDetection.reasoning.length && <p className="mt-2 text-sm text-ink/65">{shopTypeDetection.reasoning[0]}</p>}
            {shopTypeDetection.needsConfirmation && (
              <div className="mt-3 rounded-2xl bg-coral/8 px-3 py-2 text-sm text-coral">
                This category is provisional. Review and confirm the shop type before the underwriting model uses it.
              </div>
            )}
            {!!shopTypeDetection.topCandidates.length && (
              <div className="mt-4 space-y-2">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink/45">Top alternatives</p>
                {shopTypeDetection.topCandidates.map((candidate) => (
                  <div key={candidate.shopType} className="rounded-2xl bg-clay/25 px-3 py-2 text-sm text-ink/75">
                    <div className="font-medium text-ink">
                      {prettifyLabel(candidate.shopType)} - {Math.round(candidate.confidence * 100)}%
                    </div>
                    {!!candidate.reasons.length && <div className="mt-1 text-xs text-ink/60">{candidate.reasons[0]}</div>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
