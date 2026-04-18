import { useState } from "react";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";

import { login, register } from "../api/auth";
import { setAuth } from "../app/store";


export function LoginPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [email, setEmail] = useState("merchant@example.com");
  const [password, setPassword] = useState("password123");
  const [fullName, setFullName] = useState("Demo Merchant");
  const [mode, setMode] = useState<"login" | "register">("register");
  const [role, setRole] = useState("merchant");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [statusMessage, setStatusMessage] = useState("");

  async function handleSubmit() {
    setIsSubmitting(true);
    setErrorMessage("");
    setStatusMessage(mode === "register" ? "Creating your account..." : "Signing you in...");
    try {
      if (mode === "register") {
        await register(email, password, fullName, role);
        setStatusMessage("Account created. Signing you in...");
      }
      const response = await login(email, password);
      dispatch(setAuth({ accessToken: response.access_token, user: response.user }));
      setStatusMessage("Signed in successfully. Opening your workspace...");
      navigate(response.user.role === "merchant" ? "/merchant/session" : "/underwriter/queue");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Something went wrong";
      if (message.includes("409")) {
        setErrorMessage("That email is already registered. Switch to login or use another email.");
      } else if (message.includes("401")) {
        setErrorMessage("Invalid email or password.");
      } else if (message.includes("500")) {
        setErrorMessage("The server hit an internal error. Please try again in a moment.");
      } else {
        setErrorMessage("We couldn’t complete the request. Please try again.");
      }
      setStatusMessage("");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
      <div className="panel p-8">
        <p className="text-sm uppercase tracking-[0.25em] text-pine">Remote underwriting</p>
        <h1 className="mt-4 max-w-2xl text-5xl font-semibold leading-tight">A calmer starting point for kirana cash-flow underwriting.</h1>
        <p className="mt-6 max-w-xl text-lg leading-8 text-ink/70">
          Start with one account, one session, and one guided workflow. The app will walk you through images, location, underwriting, and review step by step.
        </p>
        <div className="mt-8 grid gap-3 md:grid-cols-3">
          <div className="rounded-3xl bg-clay/30 p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-ink/50">Step 1</p>
            <p className="mt-2 font-semibold">Create account</p>
            <p className="mt-2 text-sm text-ink/65">Register once and you’re in.</p>
          </div>
          <div className="rounded-3xl bg-clay/30 p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-ink/50">Step 2</p>
            <p className="mt-2 font-semibold">Upload store images</p>
            <p className="mt-2 text-sm text-ink/65">3 to 5 photos, clearly guided.</p>
          </div>
          <div className="rounded-3xl bg-clay/30 p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-ink/50">Step 3</p>
            <p className="mt-2 font-semibold">Review output</p>
            <p className="mt-2 text-sm text-ink/65">Ranges, confidence, flags, and next actions.</p>
          </div>
        </div>
      </div>
      <div className="panel p-8">
        <div className="mb-6 flex gap-2">
          <button className={mode === "register" ? "button-primary" : "button-secondary"} onClick={() => { setMode("register"); setErrorMessage(""); setStatusMessage(""); }}>Register</button>
          <button className={mode === "login" ? "button-primary" : "button-secondary"} onClick={() => { setMode("login"); setErrorMessage(""); setStatusMessage(""); }}>Login</button>
        </div>
        <div className="mb-6">
          <p className="text-sm font-medium text-ink/75">
            {mode === "register" ? "Create your first account to begin the guided flow." : "Sign in to continue where you left off."}
          </p>
        </div>
        <div className="space-y-4">
          {mode === "register" && (
            <input className="input" value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Full name" />
          )}
          <input className="input" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email" />
          <input className="input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Password" />
          {mode === "register" && (
            <select className="input" value={role} onChange={(event) => setRole(event.target.value)}>
              <option value="merchant">merchant</option>
              <option value="underwriter">underwriter</option>
              <option value="admin">admin</option>
            </select>
          )}
          {statusMessage && (
            <div className="rounded-2xl bg-pine/8 px-4 py-3 text-sm text-pine">
              <div className="flex items-center gap-3">
                {isSubmitting && <span className="h-4 w-4 animate-spin rounded-full border-2 border-pine/30 border-t-pine" />}
                <span>{statusMessage}</span>
              </div>
            </div>
          )}
          {errorMessage && (
            <div className="rounded-2xl bg-coral/10 px-4 py-3 text-sm text-coral">
              {errorMessage}
            </div>
          )}
          <button className="button-primary w-full disabled:cursor-not-allowed disabled:opacity-60" onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? (mode === "register" ? "Creating account..." : "Signing in...") : (mode === "register" ? "Create account and continue" : "Continue")}
          </button>
          <p className="text-xs text-ink/50">
            Demo defaults are already filled in, so you can register immediately and move into the product flow.
          </p>
        </div>
      </div>
    </section>
  );
}
