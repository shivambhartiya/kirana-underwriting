from app.utils.geo_math import clamp


def compute_confidence(
    interval_width_ratio: float,
    completeness: float,
    anomaly_score: float,
    quality_score: float,
) -> float:
    raw = (0.45 * completeness) + (0.35 * quality_score) + (0.20 * (1 - anomaly_score)) - (0.25 * interval_width_ratio)
    return round(clamp(raw, 0.05, 0.99), 2)

