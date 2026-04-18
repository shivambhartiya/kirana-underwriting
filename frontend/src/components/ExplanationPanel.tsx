export function ExplanationPanel({ title, text }: { title: string; text?: string }) {
  return (
    <div className="panel p-5">
      <p className="text-sm uppercase tracking-[0.2em] text-ink/50">{title}</p>
      <p className="mt-4 leading-7 text-ink/80">{text || "Explanation will appear once prediction completes."}</p>
    </div>
  );
}

