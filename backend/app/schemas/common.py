from pydantic import BaseModel, Field


class MoneyRange(BaseModel):
    min: float
    max: float
    currency: str = "INR"


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail
    request_id: str

