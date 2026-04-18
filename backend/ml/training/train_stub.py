import json
from pathlib import Path

import pandas as pd


def build_synthetic_dataset(rows: int = 200) -> pd.DataFrame:
    records = []
    for index in range(rows):
        footfall = 0.2 + ((index % 10) * 0.07)
        inventory = 0.3 + ((index % 7) * 0.08)
        diversity = 0.25 + ((index % 5) * 0.1)
        daily_sales = 3000 + (footfall * 4200) + (inventory * 1800) + (diversity * 1300)
        records.append(
            {
                "footfall_proxy": round(footfall, 3),
                "inventory_depth_score": round(inventory, 3),
                "sku_diversity_score": round(diversity, 3),
                "daily_sales_target": round(daily_sales, 2),
            }
        )
    return pd.DataFrame.from_records(records)


def main() -> None:
    dataset = build_synthetic_dataset()
    output_dir = Path(__file__).resolve().parents[1] / "model_registry" / "artifacts"
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output_dir / "synthetic_training_data.csv", index=False)
    metadata = {
        "rows": len(dataset),
        "targets": ["daily_sales_target"],
        "note": "Starter synthetic dataset for local experimentation.",
    }
    (output_dir / "training_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

