export function PredictionRangeCard({ title, range }: { title: string; range?: { min: number; max: number; currency?: string } }) {
  return (
    <div className="panel p-5">
      <p className="text-sm uppercase tracking-[0.2em] text-ink/50">{title}</p>
      <p className="mt-3 text-3xl font-semibold">
        {range ? `${range.currency || "INR"} ${Math.round(range.min).toLocaleString()} - ${Math.round(range.max).toLocaleString()}` : "Pending"}
      </p>
    </div>
  );
}

