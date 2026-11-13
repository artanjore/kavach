from sqlalchemy.orm import Session

from ..models import AuditLog


def audit(db: Session, actor: str, action: str, target: str = "", detail: str = "") -> None:
    db.add(AuditLog(actor=actor, action=action, target=target, detail=detail[:2000]))
