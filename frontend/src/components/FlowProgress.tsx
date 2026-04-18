const steps = [
  { key: "account", label: "Account" },
  { key: "images", label: "Images" },
  { key: "location", label: "Location" },
  { key: "review", label: "Underwrite" },
  { key: "results", label: "Results" },
];

export function FlowProgress({ current }: { current: string }) {
  const currentIndex = steps.findIndex((step) => step.key === current);
  return (
    <div className="panel p-5">
      <div className="flex flex-wrap gap-3">
        {steps.map((step, index) => {
          const active = index <= currentIndex;
          return (
            <div
              key={step.key}
              className={`rounded-full px-4 py-2 text-sm font-medium ${active ? "bg-pine text-white" : "bg-ink/5 text-ink/55"}`}
            >
              {index + 1}. {step.label}
            </div>
          );
        })}
      </div>
    </div>
  );
}

