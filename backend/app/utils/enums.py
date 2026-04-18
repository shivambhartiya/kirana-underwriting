from enum import Enum


class Role(str, Enum):
    merchant = "merchant"
    underwriter = "underwriter"
    admin = "admin"


class SessionStatus(str, Enum):
    draft = "draft"
    uploaded = "uploaded"
    located = "located"
    processing = "processing"
    completed = "completed"
    rejected = "rejected"


class PredictionStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class ImageRole(str, Enum):
    interior_shelf = "interior_shelf"
    counter = "counter"
    storefront = "storefront"
    street_view = "street_view"
    extra = "extra"


class RiskSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RiskSource(str, Enum):
    rule = "rule"
    anomaly = "anomaly"
    manual = "manual"


class Recommendation(str, Enum):
    approve_candidate = "approve_candidate"
    needs_verification = "needs_verification"
    reject_candidate = "reject_candidate"


class ExplainAudience(str, Enum):
    merchant = "merchant"
    underwriter = "underwriter"


class ShopType(str, Enum):
    kirana_general = "kirana_general"
    vegetable_fruit = "vegetable_fruit"
    pharmacy_medical = "pharmacy_medical"
    fast_food_qsr = "fast_food_qsr"
    religious_gifts = "religious_gifts"
    jewellery = "jewellery"
    bakery_sweets = "bakery_sweets"
    mobile_electronics = "mobile_electronics"
    apparel_boutique = "apparel_boutique"
