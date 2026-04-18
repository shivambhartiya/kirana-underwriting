import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useParams } from "react-router-dom";

import { getPrediction, simulatePrediction } from "../api/prediction";
import type { RootState } from "../app/store";
import { setPredictionResult, setSimulationResult } from "../app/store";
import { ConfidenceMeter } from "../components/ConfidenceMeter";
import { ExplanationPanel } from "../components/ExplanationPanel";
import { FlowProgress } from "../components/FlowProgress";
import { PredictionRangeCard } from "../components/PredictionRangeCard";
import { RiskFlagPanel } from "../components/RiskFlagPanel";
import { SimulationControls } from "../components/SimulationControls";

const prettifyLabel = (value: string) => (value === "religious_gifts" ? "Pooja + Gifts" : value.split("_").join(" "));

export function ResultsPage() {
  const { predictionId = "" } = useParams();
  const dispatch = useDispatch();
  const result = useSelector((state: RootState) => state.prediction.result);
  const simulation = useSelector((state: RootState) => state.simulation.result);

  useEffect(() => {
    let timer: number | undefined;

    async function poll() {
      const response = await getPrediction(predictionId);
      dispatch(setPredictionResult(response));
      if (response.status !== "completed") {
        timer = window.setTimeout(poll, 2000);
      }
    }

    void poll();
    return () => window.clearTimeout(timer);
  }, [dispatch, predictionId]);

  async function runSimulation(deltas: { delta_shelf_density: number; delta_storefront_visibility: number; delta_footfall_proxy: number }) {
    const response = await simulatePrediction({ prediction_id: predictionId, ...deltas });
    dispatch(setSimulationResult(response));
  }

  return (
    <section className="space-y-6">
      <FlowProgress current="results" />

      {result?.status !== "completed" && (
        <div className="panel p-6">
          <div className="flex items-center gap-3 text-pine">
            <span className="h-5 w-5 animate-spin rounded-full border-2 border-pine/30 border-t-pine" />
            <div>
              <p className="font-semibold">Underwriting in progress</p>
              <p className="text-sm text-ink/70">The system is combining image signals, location intelligence, and fraud checks. Results will appear automatically.</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-4">
        <PredictionRangeCard title="Daily Sales (Range)" range={result?.daily_sales_range} />
        <PredictionRangeCard title="Monthly Revenue (Range)" range={result?.monthly_revenue_range} />
        <PredictionRangeCard title="Normalized Monthly Income (Range)" range={result?.monthly_income_range} />
        <ConfidenceMeter score={result?.confidence_score || 0} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <div className="panel p-5">
            <p className="text-sm uppercase tracking-[0.2em] text-ink/50">Detected Shop Type</p>
            <p className="mt-4 text-2xl font-semibold">{result?.detected_shop_type ? prettifyLabel(result.detected_shop_type) : "Not available"}</p>
            <p className="mt-2 text-sm text-ink/60">Confidence {Math.round((result?.shop_type_confidence || 0) * 100)}% - {result?.shop_type_source || "system"}</p>
            <p className="mt-1 text-sm text-ink/60">
              {result?.shop_type_confirmed_by_user
                ? "Shop type was confirmed before underwriting."
                : result?.shop_type_needs_confirmation
                  ? "Shop type remained provisional, so the model used a conservative specialty-retail blend."
                  : "Shop type was auto-accepted for underwriting."}
            </p>
            {!!result?.shop_type_candidates?.length && (
              <div className="mt-4 space-y-2 rounded-2xl bg-clay/25 px-3 py-3 text-sm text-ink/75">
                <p className="font-semibold text-ink">Top shop-type candidates</p>
                {result.shop_type_candidates.map((candidate: any) => (
                  <div key={candidate.shop_type}>
                    <span className="font-medium">{prettifyLabel(candidate.shop_type)}</span> - {Math.round(candidate.confidence * 100)}%
                  </div>
                ))}
              </div>
            )}
          </div>

          <ExplanationPanel title="Merchant Explanation" text={result?.explanation_merchant} />
          <SimulationControls onRun={runSimulation} />

          {simulation && (
            <div className="panel p-5">
              <p className="text-sm uppercase tracking-[0.2em] text-ink/50">Simulation Output</p>
              <p className="mt-4 text-ink/75">{simulation.summary}</p>
              <div className="mt-4 grid gap-4 md:grid-cols-3">
                <PredictionRangeCard title="Sim Daily" range={simulation.revised_daily_sales_range} />
                <PredictionRangeCard title="Sim Revenue" range={simulation.revised_monthly_revenue_range} />
                <PredictionRangeCard title="Sim Income" range={simulation.revised_monthly_income_range} />
              </div>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <RiskFlagPanel flags={result?.risk_flags} />

          <div className="panel p-5">
            <p className="text-sm uppercase tracking-[0.2em] text-ink/50">Expected Output Format</p>
            <pre className="mt-4 overflow-auto rounded-2xl bg-ink/5 p-4 text-xs text-ink/75">
{JSON.stringify(
  {
    daily_sales_range: result?.daily_sales_range,
    monthly_revenue_range: result?.monthly_revenue_range,
    monthly_income_range: result?.monthly_income_range,
    confidence_score: result?.confidence_score,
    risk_flags: result?.risk_flags,
    detected_shop_type: result?.detected_shop_type,
    shop_type_confirmed_by_user: result?.shop_type_confirmed_by_user,
  },
  null,
  2,
)}
            </pre>
          </div>

          <div className="panel p-5">
            <p className="text-sm uppercase tracking-[0.2em] text-ink/50">Additional Details</p>
            <p className="mt-3 text-sm text-ink/70">
              Annual revenue run-rate: INR {Math.round(result?.annual_revenue_run_rate?.min || 0).toLocaleString()} - {Math.round(result?.annual_revenue_run_rate?.max || 0).toLocaleString()}
            </p>
            <p className="mt-2 text-sm text-ink/70">
              Annual income run-rate: INR {Math.round(result?.annual_income_run_rate?.min || 0).toLocaleString()} - {Math.round(result?.annual_income_run_rate?.max || 0).toLocaleString()}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
