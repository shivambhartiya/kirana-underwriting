from pydantic import BaseModel

from app.utils.enums import ExplainAudience


class ExplainRequest(BaseModel):
    prediction_id: str
    audience: ExplainAudience


class ExplainResponse(BaseModel):
    prediction_id: str
    audience: ExplainAudience
    top_positive_drivers: list[str]
    top_negative_drivers: list[str]
    narrative: str

