from math import asin, cos, radians, sin, sqrt


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def bounded_score(*values: float) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return clamp(mean, 0.0, 1.0)


def pseudo_radius_score(lat: float, lng: float) -> float:
    seed = abs(lat * 1000) + abs(lng * 1000)
    return clamp((seed % 100) / 100, 0.05, 0.95)


def euclidean_norm(*values: float) -> float:
    return sqrt(sum(value * value for value in values))


def interpolate(minimum: float, maximum: float, ratio: float) -> float:
    return minimum + ((maximum - minimum) * clamp(ratio, 0.0, 1.0))


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371.0
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    a = (sin(delta_lat / 2) ** 2) + (cos(lat1_rad) * cos(lat2_rad) * (sin(delta_lng / 2) ** 2))
    return 2 * radius_km * asin(sqrt(a))
