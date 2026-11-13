"""Login, profile, consent (DPDP), data export and deletion, pairing (F1)."""
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import (Alert, AuthToken, CallEvent, ConsentRecord, MessageCheck, NumberReport, Pairing, PairingCode,
                      User, now)
from ..risk.phone import normalize
from ..services import auth
from ..services.audit import audit
from ..services.privacy import NOTICE_VERSION, PURPOSES, notice

router = APIRouter(prefix="/v1", tags=["users"])


# ------------------------------------------------------------------ auth
class OtpRequest(BaseModel):
    phone: str


class OtpVerify(BaseModel):
    phone: str
    code: str = Field(min_length=6, max_length=6)
    role: str = Field(default="senior", pattern="^(senior|guardian)$")
    language: str = "hi"
    name: str = ""


@router.post("/auth/otp/request")
def otp_request(body: OtpRequest, db: Session = Depends(get_db)):
    phone = normalize(body.phone)
    if not phone.startswith("+") or len(phone) < 11:
        raise HTTPException(422, "enter a full mobile number")
    code = auth.request_otp(db, phone)
    return {"sent": True, **({"dev_code": code} if settings.is_dev else {})}


@router.post("/auth/otp/verify")
def otp_verify(body: OtpVerify, db: Session = Depends(get_db)):
    phone = normalize(body.phone)
    if not auth.verify_otp(db, phone, body.code):
        raise HTTPException(401, "wrong or expired code")
    user = db.scalar(select(User).where(User.phone == phone))
    if user and user.deleted_at:
        user.deleted_at = None
    if not user:
        user = User(phone=phone, role=body.role, language=body.language, name=body.name)
        db.add(user)
        db.commit()
    return {"token": auth.issue_token(db, user), "user": _me(user)}


# --------------------------------------------------------------- profile
class ProfileUpdate(BaseModel):
    name: str | None = None
    language: str | None = None
    whatsapp_opt_in: bool | None = None
    bank_code: str | None = None
    bank_customer_ref: str | None = None
    push_token: str | None = None


def _me(u: User) -> dict:
    return {"id": u.id, "phone": u.phone, "name": u.name, "role": u.role, "language": u.language,
            "whatsapp_opt_in": u.whatsapp_opt_in, "bank_code": u.bank_code}


@router.get("/me")
def get_me(user: User = Depends(auth.current_user)):
    return _me(user)


@router.patch("/me")
def update_me(body: ProfileUpdate, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(user, k, v)
    db.merge(user)
    db.commit()
    return _me(user)


# --------------------------------------------------------------- consent
@router.get("/privacy/notice")
def get_notice(lang: str = "hi"):
    return notice(lang)


class ConsentBody(BaseModel):
    purpose: str
    granted: bool


@router.post("/consent")
def record_consent(body: ConsentBody, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    if body.purpose not in PURPOSES:
        raise HTTPException(422, f"purpose must be one of {list(PURPOSES)}")
    db.add(ConsentRecord(user_id=user.id, purpose=body.purpose, granted=body.granted,
                         notice_version=NOTICE_VERSION, language=user.language))
    if body.purpose == "whatsapp_alerts":
        user.whatsapp_opt_in = body.granted
        db.merge(user)
    audit(db, f"user:{user.id}", "consent", body.purpose, str(body.granted))
    db.commit()
    return {"ok": True}


@router.get("/me/export")
def export_my_data(user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    """DPDP right of access: everything we hold about this user."""
    def rows(model, col):
        return [{c.name: getattr(r, c.name) for c in model.__table__.columns} for r in db.scalars(select(model).where(col == user.id))]
    return {
        "profile": _me(user),
        "consents": rows(ConsentRecord, ConsentRecord.user_id),
        "calls_flagged": rows(CallEvent, CallEvent.senior_id),
        "message_checks": rows(MessageCheck, MessageCheck.user_id),
        "reports": rows(NumberReport, NumberReport.reporter_id),
        "alerts_about_me": rows(Alert, Alert.senior_id),
    }


@router.delete("/me")
def delete_me(user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    """DPDP erasure. Personal content is deleted; the anonymous audit trail stays."""
    for model, col in ((CallEvent, CallEvent.senior_id), (MessageCheck, MessageCheck.user_id), (Alert, Alert.senior_id),
                       (Alert, Alert.guardian_id), (AuthToken, AuthToken.user_id)):
        for r in db.scalars(select(model).where(col == user.id)):
            db.delete(r)
    for p in db.scalars(select(Pairing).where((Pairing.senior_id == user.id) | (Pairing.guardian_id == user.id))):
        p.status, p.revoked_at = "revoked", now()
    u = db.get(User, user.id)
    u.deleted_at = now()
    u.name, u.push_token, u.bank_customer_ref = "", "", ""
    u.phone = f"deleted:{u.id}:{secrets.token_hex(4)}"
    audit(db, f"user:{user.id}", "delete_account")
    db.commit()
    return {"deleted": True}


# --------------------------------------------------------------- pairing
@router.post("/pairing/code")
def create_pairing_code(user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    """The senior shows this 6-digit code (or a QR of it) to the guardian."""
    if user.role != "senior":
        raise HTTPException(403, "only the senior can invite a guardian")
    code = f"{secrets.randbelow(10**6):06d}"
    db.add(PairingCode(code=code, senior_id=user.id, expires_at=now() + timedelta(minutes=15)))
    db.commit()
    return {"code": code, "expires_in_s": 900}


class JoinBody(BaseModel):
    code: str


@router.post("/pairing/join")
def join_pairing(body: JoinBody, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    if user.role != "guardian":
        raise HTTPException(403, "only a guardian can join")
    pc = db.get(PairingCode, body.code)
    if not pc or pc.used or pc.expires_at < now():
        raise HTTPException(404, "code not found or expired")
    pc.used = True
    existing = db.scalar(select(Pairing).where(Pairing.senior_id == pc.senior_id, Pairing.guardian_id == user.id))
    if existing:
        existing.status, existing.revoked_at = "active", None
        p = existing
    else:
        p = Pairing(senior_id=pc.senior_id, guardian_id=user.id)
        db.add(p)
    audit(db, f"user:{user.id}", "pair_join", f"senior:{pc.senior_id}")
    db.commit()
    return _pairing(p, db)


def _pairing(p: Pairing, db: Session) -> dict:
    s, g = db.get(User, p.senior_id), db.get(User, p.guardian_id)
    return {
        "id": p.id, "status": p.status,
        "senior": {"id": s.id, "name": s.name, "phone": s.phone},
        "guardian": {"id": g.id, "name": g.name, "phone": g.phone},
        "permissions": {k: getattr(p, k) for k in ("see_call_warnings", "see_help_presses", "see_message_checks", "approve_transfers")},
        "approve_transfers_effective_at": p.approve_transfers_effective_at.isoformat() if p.approve_transfers_effective_at else None,
    }


@router.get("/pairing")
def list_pairings(user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    col = Pairing.senior_id if user.role == "senior" else Pairing.guardian_id
    return [_pairing(p, db) for p in db.scalars(select(Pairing).where(col == user.id, Pairing.status == "active"))]


class Permissions(BaseModel):
    see_call_warnings: bool | None = None
    see_help_presses: bool | None = None
    see_message_checks: bool | None = None
    approve_transfers: bool | None = None


@router.patch("/pairing/{pairing_id}")
def set_permissions(pairing_id: int, body: Permissions, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    """Only the senior changes what a guardian can see or approve."""
    p = db.get(Pairing, pairing_id)
    if not p or p.senior_id != user.id or p.status != "active":
        raise HTTPException(404, "pairing not found")
    changes = body.model_dump(exclude_none=True)
    if changes.get("approve_transfers") and not p.approve_transfers:
        p.approve_transfers_effective_at = now() + timedelta(hours=settings.guardian_approval_cooloff_hours)
    if changes.get("approve_transfers") is False:
        p.approve_transfers_effective_at = None
    for k, v in changes.items():
        setattr(p, k, v)
    audit(db, f"user:{user.id}", "pair_permissions", f"pairing:{p.id}", str(changes))
    db.commit()
    return _pairing(p, db)


@router.delete("/pairing/{pairing_id}")
def remove_pairing(pairing_id: int, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    """Senior can remove a guardian, or a guardian can leave, at any time, immediately."""
    p = db.get(Pairing, pairing_id)
    if not p or user.id not in (p.senior_id, p.guardian_id):
        raise HTTPException(404, "pairing not found")
    p.status, p.revoked_at = "revoked", now()
    p.approve_transfers, p.approve_transfers_effective_at = False, None
    audit(db, f"user:{user.id}", "pair_remove", f"pairing:{p.id}")
    db.commit()
    return {"removed": True}
