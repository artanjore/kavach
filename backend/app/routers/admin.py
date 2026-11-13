"""MVP success metrics (see PRD) for the founding team. Protected by ADMIN_TOKEN."""
import os
import statistics
from datetime import timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Alert, CallEvent, MessageCheck, Pairing, User, now

router = APIRouter(prefix="/v1/admin", tags=["admin"])


def admin(x_admin_token: str = Header(default="")):
    expected = os.environ.get("ADMIN_TOKEN", "dev-admin" if settings.is_dev else "")
    if not expected or x_admin_token != expected:
        raise HTTPException(401, "admin only")


@router.get("/metrics", dependencies=[Depends(admin)])
def metrics(db: Session = Depends(get_db)):
    t = now()
    week = t - timedelta(days=7)
    pairs = db.scalars(select(Pairing).where(Pairing.status == "active")).all()
    activated_seniors = {p.senior_id for p in pairs}

    active = set(db.scalars(select(CallEvent.senior_id).where(CallEvent.created_at >= week)))
    active |= set(db.scalars(select(MessageCheck.user_id).where(MessageCheck.created_at >= week)))
    active |= set(db.scalars(select(Alert.senior_id).where(Alert.created_at >= week, Alert.kind.in_(["help_pressed", "checklist_yes"]))))
    weekly_active = len(active & activated_seniors)

    warned = db.scalars(select(CallEvent).where(CallEvent.level == "warn")).all()
    labelled = [c for c in warned if c.outcome]
    precision = sum(c.outcome == "scam" for c in labelled) / len(labelled) if labelled else None
    false_alarm = sum(c.outcome == "genuine" for c in warned) / len(warned) if warned else None

    resp = [(a.called_back_at - a.created_at).total_seconds() / 60 for a in db.scalars(select(Alert).where(Alert.called_back_at.is_not(None)))]

    old = [p for p in pairs if p.created_at <= t - timedelta(days=90)]
    return {
        "activated_pairs": len(pairs),
        "weekly_active_seniors": weekly_active,
        "weekly_active_share": weekly_active / len(activated_seniors) if activated_seniors else None,
        "call_warnings": len(warned),
        "alert_precision": precision,
        "false_alarm_rate": false_alarm,
        "median_guardian_response_min": statistics.median(resp) if resp else None,
        "pairs_older_than_90d": len(old),
        "message_checks": len(db.scalars(select(MessageCheck.id)).all()),
        "seniors": len(db.scalars(select(User.id).where(User.role == "senior", User.deleted_at.is_(None))).all()),
    }
