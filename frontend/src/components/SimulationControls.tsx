type Props = {
  onRun: (payload: { delta_shelf_density: number; delta_storefront_visibility: number; delta_footfall_proxy: number }) => void;
};

export function SimulationControls({ onRun }: Props) {
  return (
    <div className="panel p-5">
      <p className="text-sm uppercase tracking-[0.2em] text-ink/50">Simulation</p>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <button className="button-secondary" onClick={() => onRun({ delta_shelf_density: 0.08, delta_storefront_visibility: 0, delta_footfall_proxy: 0 })}>
          Better shelves
        </button>
        <button className="button-secondary" onClick={() => onRun({ delta_shelf_density: 0, delta_storefront_visibility: 0.06, delta_footfall_proxy: 0 })}>
          Better frontage
        </button>
        <button className="button-secondary" onClick={() => onRun({ delta_shelf_density: 0, delta_storefront_visibility: 0, delta_footfall_proxy: 0.08 })}>
          Better footfall
        </button>
      </div>
    </div>
  );
}
