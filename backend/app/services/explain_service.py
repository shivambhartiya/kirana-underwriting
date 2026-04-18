from app.schemas.explain import ExplainResponse
from app.utils.enums import ExplainAudience


class ExplainService:
    def generate(self, prediction_id: str, visual_features: dict, geo_features: dict, confidence_score: float, audience: ExplainAudience) -> ExplainResponse:
        positives = []
        negatives = []
        shop_type = visual_features.get("detected_shop_type") or "general retail"
        display_shop_type = "pooja + gifts" if shop_type == "religious_gifts" else shop_type.replace("_", " ")
        shop_type_confirmed = bool(visual_features.get("shop_type_confirmed_by_user") or False)
        shop_type_needs_confirmation = bool(visual_features.get("shop_type_needs_confirmation") or False)
        if visual_features.get("shelf_density_index", 0) > 0.6:
            positives.append("Strong shelf utilization indicates active working capital deployment.")
        if visual_features.get("sku_diversity_score", 0) > 0.5:
            positives.append("Broad SKU coverage suggests wider footfall capture.")
        if geo_features.get("footfall_proxy", 0) < 0.4:
            negatives.append("External demand appears constrained by modest location activity.")
        if confidence_score < 0.65:
            negatives.append("Confidence is reduced by limited coverage or feature uncertainty.")
        if shop_type_needs_confirmation and not shop_type_confirmed:
            negatives.append("Shop type remained provisional, so conservative specialty-retail priors were used.")

        if audience == ExplainAudience.merchant:
            type_intro = (
                f"The system used your confirmed shop type of {display_shop_type}."
                if shop_type_confirmed
                else f"The current shop type estimate is {display_shop_type}."
            )
            narrative = (
                f"{type_intro} Monthly performance ranges were calibrated from store readiness, location demand, and shop-type-specific priors. "
                "The model now anchors revenue on a conservative monthly retail band before estimating normalized income. "
                "Confidence improves when the storefront, street context, and optional business details are clearly captured."
            )
        else:
            type_intro = (
                f"Shop type was user-confirmed as {display_shop_type}."
                if shop_type_confirmed
                else f"Shop type remained model-estimated as {display_shop_type}."
            )
            narrative = (
                f"{type_intro} Model output blends shop-type priors, visual inventory proxies, and geo demand context. "
                "Current ranges are supported by shelf density, SKU breadth, catchment signals, and optional business inputs, with monthly revenue capped by store-size and demand realism. Confidence is moderated by coverage completeness, anomaly checks, geo confidence, and shop-type certainty."
            )
        return ExplainResponse(
            prediction_id=prediction_id,
            audience=audience,
            top_positive_drivers=positives,
            top_negative_drivers=negatives,
            narrative=narrative,
        )
