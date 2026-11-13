"""v2: bank risk events + trusted-person approval (F9) and bank dashboard (F11).

Flow: the bank pauses a risky transfer by an enrolled senior and POSTs a risk
event. We alert the senior's trusted guardians; one of them approves or
declines in the app. We tell the bank (callback + pollable status). If nobody
decides before expiry, the status becomes "expired" and the bank applies its
own default. We never move or hold money ourselves.
"""
import logging
from datetime import timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Alert, AuditLog, Pairing, TransferHold, User, now
from ..services import auth
from ..services.alerts import notify_guardians
from ..services.audit import audit

router = APIRouter(prefix="/v1", tags=["bank"])
log = logging.getLogger(__name__)


class RiskEvent(BaseModel):
    event_id: str = Field(max_length=64)
    customer_ref: str
    amount_paise: int = Field(gt=0)
    payee_label: str = ""
    first_time_payee: bool = False
    callback_url: str = ""


def _hold_json(h: TransferHold) -> dict:
    return {"hold_id": h.id, "event_id": h.bank_event_id, "status": h.status, "amount_paise": h.amount_paise,
            "payee_label": h.payee_label, "expires_at": h.expires_at.isoformat(),
            "decided_at": h.decided_at.isoformat() if h.decided_at else None}


def _expire(db: Session, h: TransferHold) -> None:
    if h.status == "pending" and h.expires_at < now():
        h.status = "expired"
        audit(db, "system", "hold_expired", f"hold:{h.id}")
        db.commit()
        _callback(db, h)


def trusted_guardians(db: Session, senior_id: int) -> list[User]:
    rows = db.scalars(select(Pairing).where(Pairing.senior_id == senior_id, Pairing.status == "active",
                                            Pairing.approve_transfers.is_(True))).all()
    t = now()
    return [db.get(User, p.guardian_id) for p in rows
            if p.approve_transfers_effective_at and p.approve_transfers_effective_at <= t]


@router.post("/bank/risk-events")
def risk_event(body: RiskEvent, bank: str = Depends(auth.bank_caller), db: Session = Depends(get_db)):
    existing = db.scalar(select(TransferHold).where(TransferHold.bank_code == bank, TransferHold.bank_event_id == body.event_id))
    if existing:  # idempotent
        _expire(db, existing)
        return _hold_json(existing)
    senior = db.scalar(select(User).where(User.bank_code == bank, User.bank_customer_ref == body.customer_ref,
                                          User.deleted_at.is_(None)))
    if not senior:
        raise HTTPException(404, "customer not enrolled")
    guardians = trusted_guardians(db, senior.id)
    if not guardians:
        audit(db, f"bank:{bank}", "risk_event_no_trusted_person", f"user:{senior.id}", body.event_id)
        db.commit()
        return {"status": "no_trusted_person", "event_id": body.event_id}

    h = TransferHold(bank_code=bank, bank_event_id=body.event_id, senior_id=senior.id, amount_paise=body.amount_paise,
                     payee_label=body.payee_label, first_time_payee=body.first_time_payee, callback_url=body.callback_url,
                     expires_at=now() + timedelta(minutes=settings.hold_decision_minutes))
    db.add(h)
    db.flush()
    audit(db, f"bank:{bank}", "risk_event", f"hold:{h.id}", f"amount_paise={body.amount_paise}")
    db.commit()
    notify_guardians(db, senior, "transfer_hold", ref_id=h.id, guardians=guardians, bank=bank,
                     amount=f"{body.amount_paise / 100:,.0f}", payee=body.payee_label or "a new payee",
                     minutes=settings.hold_decision_minutes)
    return _hold_json(h)


@router.get("/bank/holds/{event_id}")
def hold_status(event_id: str, bank: str = Depends(auth.bank_caller), db: Session = Depends(get_db)):
    h = db.scalar(select(TransferHold).where(TransferHold.bank_code == bank, TransferHold.bank_event_id == event_id))
    if not h:
        raise HTTPException(404, "not found")
    _expire(db, h)
    return _hold_json(h)


@router.get("/bank/dashboard")
def dashboard(bank: str = Depends(auth.bank_caller), db: Session = Depends(get_db)):
    enrolled = db.scalar(select(func.count()).select_from(User).where(User.bank_code == bank, User.deleted_at.is_(None))) or 0
    by_status = dict(db.execute(select(TransferHold.status, func.count()).where(TransferHold.bank_code == bank)
                                .group_by(TransferHold.status)).all())
    senior_ids = select(User.id).where(User.bank_code == bank)
    alerts = dict(db.execute(select(Alert.kind, func.count()).where(Alert.senior_id.in_(senior_ids))
                             .group_by(Alert.kind)).all())
    prevented = db.scalar(select(func.sum(TransferHold.amount_paise)).where(TransferHold.bank_code == bank,
                                                                            TransferHold.status == "declined")) or 0
    log_rows = db.scalars(select(AuditLog).where(AuditLog.actor == f"bank:{bank}").order_by(AuditLog.id.desc()).limit(50)).all()
    recent = db.scalars(select(TransferHold).where(TransferHold.bank_code == bank).order_by(TransferHold.id.desc()).limit(25)).all()
    for h in recent:
        _expire(db, h)
    return {"enrolled_seniors": enrolled, "recent_holds": [_hold_json(h) for h in recent], "holds_by_status": by_status, "alerts_by_kind": alerts,
            "declined_amount_rupees": prevented / 100,
            "audit": [{"at": a.created_at.isoformat(), "action": a.action, "target": a.target} for a in log_rows]}


# ------------------------------------------------------- guardian side
@router.get("/holds")
def my_holds(user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    seniors = [p.senior_id for p in db.scalars(select(Pairing).where(Pairing.guardian_id == user.id, Pairing.status == "active"))]
    rows = db.scalars(select(TransferHold).where(TransferHold.senior_id.in_(seniors)).order_by(TransferHold.id.desc()).limit(50)).all()
    for h in rows:
        _expire(db, h)
    return [{**_hold_json(h), "senior": db.get(User, h.senior_id).name, "bank": h.bank_code} for h in rows]


class Decision(BaseModel):
    decision: str = Field(pattern="^(approve|decline)$")
    note: str = ""


@router.post("/holds/{hold_id}/decision")
def decide(hold_id: int, body: Decision, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    h = db.get(TransferHold, hold_id)
    if not h:
        raise HTTPException(404, "not found")
    if user.id not in {g.id for g in trusted_guardians(db, h.senior_id)}:
        raise HTTPException(403, "you are not a trusted person for this account")
    _expire(db, h)
    if h.status != "pending":
        raise HTTPException(409, f"already {h.status}")
    h.status = "approved" if body.decision == "approve" else "declined"
    h.decided_by, h.decided_at, h.decision_note = user.id, now(), body.note[:500]
    audit(db, f"user:{user.id}", f"hold_{h.status}", f"hold:{h.id}")
    db.commit()
    _callback(db, h)
    return _hold_json(h)


def _callback(db: Session, h: TransferHold) -> None:
    if not h.callback_url or settings.is_dev:
        return
    try:
        httpx.post(h.callback_url, json=_hold_json(h), timeout=5)
    except httpx.HTTPError as e:  # the bank can still poll /bank/holds/{event_id}
        log.warning("bank callback failed for hold %s: %s", h.id, e)
