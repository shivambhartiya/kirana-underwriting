import { api } from "./client";

export function createPrediction(payload: unknown) {
  return api<{ prediction_id: string; status: string }>("/predict", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getPrediction(predictionId: string) {
  return api<any>(`/predict/${predictionId}`);
}

export function explainPrediction(payload: unknown) {
  return api("/explain", { method: "POST", body: JSON.stringify(payload) });
}

export function simulatePrediction(payload: unknown) {
  return api("/simulate", { method: "POST", body: JSON.stringify(payload) });
}

export function fraudCheck(payload: unknown) {
  return api("/fraud-check", { method: "POST", body: JSON.stringify(payload) });
}

