import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";

import { createSession } from "../api/uploads";
import type { RootState } from "../app/store";
import { setSessionId } from "../app/store";


export function MerchantSessionPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const sessionId = useSelector((state: RootState) => state.session.sessionId);

  async function handleStart() {
    try {
      const response = await createSession();
      dispatch(setSessionId(response.session_id));
      navigate("/merchant/upload");
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      alert(`Failed to create session: ${msg}`);
    }
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
      <div className="panel p-8">
        <p className="text-sm uppercase tracking-[0.2em] text-pine">Merchant capture</p>
        <h2 className="mt-4 text-4xl font-semibold">Start a new underwriting session</h2>
        <p className="mt-4 max-w-2xl text-ink/70">
          You will upload 3-5 photos, share the shop location, and receive an underwriting-ready sales and income range with confidence and flags.
        </p>
        <button className="button-primary mt-6" onClick={handleStart}>Create session</button>
      </div>
      <div className="panel p-8">
        <p className="text-sm uppercase tracking-[0.2em] text-ink/50">Current state</p>
        <p className="mt-4 text-lg">Session ID: {sessionId || "No active session yet"}</p>
      </div>
    </section>
  );
}

