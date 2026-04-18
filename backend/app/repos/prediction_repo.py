from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prediction import Prediction
from app.models.risk_flag import RiskFlag


class PredictionRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, prediction: Prediction) -> Prediction:
        self.db.add(prediction)
        self.db.commit()
        self.db.refresh(prediction)
        return prediction

    def get(self, prediction_id: str) -> Prediction | None:
        return self.db.get(Prediction, prediction_id)

    def save(self, prediction: Prediction) -> Prediction:
        self.db.add(prediction)
        self.db.commit()
        self.db.refresh(prediction)
        return prediction

    def list_flags(self, prediction_id: str) -> list[RiskFlag]:
        return list(self.db.scalars(select(RiskFlag).where(RiskFlag.prediction_id == prediction_id)))

