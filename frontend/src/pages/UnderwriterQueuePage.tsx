import { Link } from "react-router-dom";
import { useSelector } from "react-redux";

import type { RootState } from "../app/store";


export function UnderwriterQueuePage() {
  const prediction = useSelector((state: RootState) => state.prediction.result);
  const predictionId = useSelector((state: RootState) => state.prediction.predictionId);

  return (
    <section className="space-y-6">
      <div className="panel p-8">
        <p className="text-sm uppercase tracking-[0.2em] text-pine">Underwriter Queue</p>
        <h2 className="mt-4 text-3xl font-semibold">Review remotely captured kirana cases</h2>
        <p className="mt-4 text-ink/70">This starter queue is seeded from the latest local session result so you can test the review surface immediately.</p>
      </div>
      <div className="panel p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-semibold">{predictionId || "No prediction yet"}</p>
            <p className="text-sm text-ink/60">{prediction?.recommendation || "Awaiting prediction"}</p>
          </div>
          {predictionId && <Link className="button-primary" to={`/underwriter/case/${predictionId}`}>Open case</Link>}
        </div>
      </div>
    </section>
  );
}

