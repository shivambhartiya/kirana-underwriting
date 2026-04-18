class BenchmarkService:
    def benchmark(self, revenue_midpoint: float, geo_features: dict) -> dict:
        density = geo_features.get("catchment_density", 0.5)
        peer_group = (
            "urban_residential_medium_density"
            if density >= 0.5
            else "semi_urban_low_density"
        )
        percentile = min(95, max(12, int((revenue_midpoint / 300000) * 100)))
        return {"peer_group": peer_group, "estimated_revenue_percentile": percentile}

