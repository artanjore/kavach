"""Dev-only helpers for the web prototype (/demo). Disabled unless KAVACH_ENV=dev."""
import secrets
from datetime import timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import ConsentRecord, OutboundMessage, Pairing, User, now
from ..services import auth

STATIC = Path(__file__).resolve().parent.parent / "static"
router = APIRouter(tags=["demo"])


def dev_only():
    if not settings.is_dev:
        raise HTTPException(404, "not found")


@router.get("/demo", include_in_schema=False, dependencies=[Depends(dev_only)])
def demo_page():
    return FileResponse(STATIC / "demo.html")


@router.get("/bank", include_in_schema=False)
def bank_page():
    """Bank partner console. Works in production too: it only calls the bank API with the key typed in."""
    return FileResponse(STATIC / "bank.html")


@router.post("/v1/demo/setup", dependencies=[Depends(dev_only)])
def setup(senior_lang: str = "hi", db: Session = Depends(get_db)):
    """Create a fresh, fully set-up senior + guardian pair enrolled with the dev bank."""
    tag = secrets.randbelow(10**6)
    senior = User(phone=f"+9170{tag:08d}", name="Kamla-ji", role="senior", language=senior_lang,
                  bank_code="DEVBANK", bank_customer_ref=f"DEMO-{tag:06d}", whatsapp_opt_in=True)
    guardian = User(phone=f"+9180{tag:08d}", name="Rohit", role="guardian", language="en", whatsapp_opt_in=True)
    db.add_all([senior, guardian])
    db.flush()
    db.add(Pairing(senior_id=senior.id, guardian_id=guardian.id, see_message_checks=True,
                   approve_transfers=True, approve_transfers_effective_at=now() - timedelta(minutes=1)))
    for u in (senior, guardian):
        for purpose in ("core_protection", "whatsapp_alerts"):
            db.add(ConsentRecord(user_id=u.id, purpose=purpose, granted=True, notice_version="demo", language=u.language))
    db.commit()
    return {
        "senior": {"token": auth.issue_token(db, senior), "phone": senior.phone, "name": senior.name,
                   "customer_ref": senior.bank_customer_ref, "language": senior.language},
        "guardian": {"token": auth.issue_token(db, guardian), "phone": guardian.phone, "name": guardian.name},
        "bank": {"code": "DEVBANK", "api_key": "dev-bank-key"},
    }


@router.get("/v1/demo/outbox", dependencies=[Depends(dev_only)])
def outbox(to: str, after_id: int = 0, db: Session = Depends(get_db)):
    """Messages we 'sent' to a number (WhatsApp is not really sent in dev)."""
    rows = db.scalars(select(OutboundMessage).where(OutboundMessage.to == to, OutboundMessage.id > after_id)
                      .order_by(OutboundMessage.id)).all()
    return [{"id": m.id, "channel": m.channel, "body": m.body, "at": m.created_at.isoformat()} for m in rows]
