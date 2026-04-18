import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { explainPrediction, fraudCheck, getPrediction } from "../api/prediction";
import { ExplanationPanel } from "../components/ExplanationPanel";
import { PredictionRangeCard } from "../components/PredictionRangeCard";
import { RiskFlagPanel } from "../components/RiskFlagPanel";


export function UnderwriterCasePage() {
  const { predictionId = "" } = useParams();
  const [result, setResult] = useState<any>(null);
  const [fraud, setFraud] = useState<any>(null);
  const [explanation, setExplanation] = useState<any>(null);

  useEffect(() => {
    async function load() {
      const [prediction, fraudResult, explainResult] = await Promise.all([
        getPrediction(predictionId),
        fraudCheck({ prediction_id: predictionId }),
        explainPrediction({ prediction_id: predictionId, audience: "underwriter" }),
      ]);
      setResult(prediction);
      setFraud(fraudResult);
      setExplanation(explainResult);
    }
    void load();
  }, [predictionId]);

  return (
    <section className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <PredictionRangeCard title="Daily Sales" range={result?.daily_sales_range} />
        <PredictionRangeCard title="Monthly Revenue" range={result?.monthly_revenue_range} />
        <PredictionRangeCard title="Monthly Income" range={result?.monthly_income_range} />
      </div>
      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <ExplanationPanel title="Underwriter Rationale" text={explanation?.narrative || result?.explanation_underwriter} />
          <div className="panel p-5">
            <p className="text-sm uppercase tracking-[0.2em] text-ink/50">Benchmark</p>
            <p className="mt-4">Peer group: {result?.benchmark?.peer_group || "N/A"}</p>
            <p className="mt-2">Revenue percentile: {result?.benchmark?.estimated_revenue_percentile || 0}</p>
          </div>
        </div>
        <div className="space-y-6">
          <RiskFlagPanel flags={result?.risk_flags} />
          <div className="panel p-5">
            <p className="text-sm uppercase tracking-[0.2em] text-ink/50">Fraud Review</p>
            <p className="mt-4">Anomaly score: {fraud?.anomaly_score || 0}</p>
            <p className="mt-2">Recommendation: {fraud?.recommendation || "pending"}</p>
          </div>
        </div>
      </div>
    </section>
  );
}

