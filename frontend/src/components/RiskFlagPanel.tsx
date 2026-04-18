export function RiskFlagPanel({ flags }: { flags?: { code: string; severity: string }[] }) {
  return (
    <div className="panel p-5">
      <p className="text-sm uppercase tracking-[0.2em] text-ink/50">Risk Flags</p>
      <div className="mt-4 space-y-2">
        {(flags || []).length ? (flags || []).map((flag) => (
          <div key={flag.code} className="rounded-2xl bg-coral/10 px-4 py-3 text-sm">
            <span className="font-semibold">{flag.code}</span> · {flag.severity}
          </div>
        )) : <p className="text-sm text-ink/70">No flags triggered.</p>}
      </div>
    </div>
  );
}

