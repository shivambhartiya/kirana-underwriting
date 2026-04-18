import { api, uploadBinary } from "./client";

export function createSession() {
  return api<{ session_id: string; status: string }>("/sessions", { method: "POST" });
}

export function initUploads(payload: unknown) {
  return api<{
    session_id: string;
    uploads: { object_key: string; upload_url: string; role: string }[];
  }>("/upload-images/init", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function suggestImageRoles(filenames: string[], imageHints: unknown[] = []) {
  return api<{ suggestions: { filename: string; suggested_role: string; confidence: number; reason: string }[] }>(
    "/upload-images/suggest-roles",
    {
      method: "POST",
      body: JSON.stringify({ filenames, image_hints: imageHints }),
    },
  );
}

export function suggestShopType(filenames: string[], imageHints: unknown[] = []) {
  return api<{
    detected_shop_type: string;
    confidence: number;
    source: string;
    reasoning: string[];
    top_candidates: { shop_type: string; confidence: number; reasons: string[] }[];
    needs_confirmation: boolean;
  }>(
    "/upload-images/suggest-shop-type",
    {
      method: "POST",
      body: JSON.stringify({ filenames, image_hints: imageHints }),
    },
  );
}

export async function performDirectUploads(
  descriptors: { upload_url: string }[],
  files: File[],
) {
  const results = await Promise.allSettled(
    descriptors.map((descriptor, index) => uploadBinary(descriptor.upload_url, files[index])),
  );
  results.forEach((result) => {
    if (result.status === "rejected") {
      console.warn("Direct upload failed in local mode; continuing with metadata-only flow.", result.reason);
    }
  });
}

export function completeUploads(payload: unknown) {
  return api("/upload-images/complete", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
