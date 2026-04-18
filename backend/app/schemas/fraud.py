from pydantic import BaseModel

from app.utils.enums import Recommendation, RiskSeverity


class FraudCheckRequest(BaseModel):
    prediction_id: str | None = None
    session_id: str | None = None


class FraudFlag(BaseModel):
    code: str
    severity: RiskSeverity
    details: dict


class FraudCheckResponse(BaseModel):
    anomaly_score: float
    recommendation: Recommendation
    triggered_flags: list[FraudFlag]

