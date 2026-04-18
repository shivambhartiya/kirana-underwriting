export function ConfidenceMeter({ score = 0 }: { score?: number }) {
  return (
    <div className="panel p-5">
      <p className="text-sm uppercase tracking-[0.2em] text-ink/50">Confidence</p>
      <div className="mt-4 h-3 rounded-full bg-ink/10">
        <div className="h-3 rounded-full bg-amber" style={{ width: `${score * 100}%` }} />
      </div>
      <p className="mt-3 text-2xl font-semibold">{Math.round(score * 100)}%</p>
    </div>
  );
}

