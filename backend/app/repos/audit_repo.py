from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, audit: AuditLog) -> AuditLog:
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        return audit

