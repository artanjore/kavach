"""Guardian alert fan-out (F4). Respects what the senior chose to share."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Alert, Pairing, User
from . import messaging
from .i18n import t

# alert kind -> pairing permission that must be on
PERMISSION = {
    "call_warning": "see_call_warnings",
    "long_call": "see_call_warnings",
    "help_pressed": "see_help_presses",
    "checklist_yes": "see_help_presses",
    "message_scam": "see_message_checks",
    "transfer_hold": "approve_transfers",
}


def active_guardians(db: Session, senior_id: int, kind: str) -> list[tuple[Pairing, User]]:
    perm = PERMISSION[kind]
    rows = db.execute(
        select(Pairing, User).join(User, User.id == Pairing.guardian_id)
        .where(Pairing.senior_id == senior_id, Pairing.status == "active", User.deleted_at.is_(None))
    ).all()
    return [(p, u) for p, u in rows if getattr(p, perm)]


def notify_guardians(db: Session, senior: User, kind: str, ref_id: int | None = None, guardians=None, **fmt) -> list[Alert]:
    alerts = []
    targets = guardians if guardians is not None else [u for _, u in active_guardians(db, senior.id, kind)]
    for g in targets:
        text = t(f"alert.{kind}", g.language, senior=senior.name or senior.phone, **fmt)
        alert = Alert(senior_id=senior.id, guardian_id=g.id, kind=kind, detail=text, ref_id=ref_id)
        db.add(alert)
        db.flush()
        if g.whatsapp_opt_in:
            messaging.send_whatsapp_alert(db, g.phone, f"{text} Call: {senior.phone}", g.language)
        messaging.send_push(db, g.push_token, "Kavach", text, {"alert_id": alert.id, "kind": kind, "call": senior.phone})
        alerts.append(alert)
    db.commit()
    return alerts
