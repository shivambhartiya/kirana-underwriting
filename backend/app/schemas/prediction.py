from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import MoneyRange
from app.schemas.upload import ShopTypeCandidate
from app.utils.enums import PredictionStatus, Recommendation, RiskSeverity, ShopType


class OptionalInputs(BaseModel):
    shop_type: ShopType | None = None
    shop_size_sqft: float | None = None
    monthly_rent: float | None = None
    years_in_operation: float | None = None
    video_duration_seconds: float | None = None
    shop_type_confidence: float | None = None
    shop_type_source: str | None = None
    shop_type_candidates: list[ShopTypeCandidate] = Field(default_factory=list)
    shop_type_needs_confirmation: bool | None = None
    shop_type_confirmed_by_user: bool | None = None


class ConsentPayload(BaseModel):
    credit_model_processing: bool = True


class PredictRequest(BaseModel):
    session_id: str
    optional_inputs: OptionalInputs | None = None
    consent: ConsentPayload


class PredictResponse(BaseModel):
    prediction_id: str
    status: PredictionStatus


class RiskFlagResponse(BaseModel):
    code: str
    severity: RiskSeverity


class EligibilityResponse(BaseModel):
    suggested_loan_amount_range: MoneyRange
    max_safe_emi: float
    suggested_tenure_months: int


class BenchmarkResponse(BaseModel):
    peer_group: str
    estimated_revenue_percentile: int


class ModelVersionResponse(BaseModel):
    vision: str
    geo: str
    underwriting: str


class PredictionResultResponse(BaseModel):
    prediction_id: str
    status: PredictionStatus
    detected_shop_type: ShopType | None = None
    shop_type_confidence: float | None = None
    shop_type_source: str | None = None
    shop_type_candidates: list[ShopTypeCandidate] = Field(default_factory=list)
    shop_type_needs_confirmation: bool = False
    shop_type_confirmed_by_user: bool = False
    daily_sales_range: MoneyRange | None = None
    monthly_revenue_range: MoneyRange | None = None
    monthly_income_range: MoneyRange | None = None
    annual_revenue_run_rate: MoneyRange | None = None
    annual_income_run_rate: MoneyRange | None = None
    confidence_score: float | None = None
    risk_flags: list[RiskFlagResponse] = Field(default_factory=list)
    recommendation: Recommendation | None = None
    eligibility: EligibilityResponse | None = None
    benchmark: BenchmarkResponse | None = None
    model_versions: ModelVersionResponse | None = None
    explanation_merchant: str | None = None
    explanation_underwriter: str | None = None
    created_at: datetime | None = None
