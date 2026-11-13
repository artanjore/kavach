"""Senior protection endpoints: F2 call screen, F3 help, F5 checker, F6 long call,
F7 report & recover, plus guardian alert inbox (F4)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Alert, CallEvent, MessageCheck, NumberReport, Pairing, ScamNumber, User, now
from ..risk import engine
from ..risk.phone import normalize
from ..services import auth
from ..services.alerts import notify_guardians
from ..services.i18n import T, reason, t

router = APIRouter(prefix="/v1", tags=["protect"])


def _senior(user: User) -> User:
    if user.role != "senior":
        raise HTTPException(403, "senior only")
    return user


# ------------------------------------------------------------ F2 screening
class ScreenBody(BaseModel):
    number: str
    cnap_name: str | None = None  # network-verified caller name, if the phone shows one


@router.post("/calls/screen")
def screen_call(body: ScreenBody, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    """Called by the Android CallScreeningService for calls from numbers not in contacts.

    The app must answer the OS within ~5 s, so it calls this with a short timeout
    and falls back to its cached scam list.
    """
    senior = _senior(user)
    a = engine.assess_call(db, senior.id, body.number)
    ev = CallEvent(senior_id=senior.id, number=a.number, level=a.level, reason_code=",".join(a.reasons))
    db.add(ev)
    db.commit()
    if a.level == "warn":
        notify_guardians(db, senior, "call_warning", ref_id=ev.id, number=a.number)
    return {
        "call_id": ev.id, "level": a.level, "reasons": a.reasons,
        "speak": t(f"call.{a.level}", senior.language),
        "reason_text": "; ".join(reason(r, senior.language) for r in a.reasons),
        "cnap_name": body.cnap_name,
    }


class CallOutcome(BaseModel):
    outcome: str  # genuine | scam


@router.post("/calls/{call_id}/outcome")
def call_outcome(call_id: int, body: CallOutcome, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    """'This was genuine' / 'This was a scam' feedback. Feeds alert precision and the number list."""
    ev = db.get(CallEvent, call_id)
    if not ev or ev.senior_id != user.id or body.outcome not in ("genuine", "scam"):
        raise HTTPException(404, "call not found")
    ev.outcome = body.outcome
    db.commit()
    _report(db, user, ev.number, body.outcome)
    return {"ok": True}


class LongCallBody(BaseModel):
    call_id: int | None = None
    number: str
    duration_s: int


@router.post("/calls/long-call")
def long_call(body: LongCallBody, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    """F6: the app reports an unknown-number call still running past the threshold."""
    senior = _senior(user)
    if body.duration_s < settings.long_call_seconds:
        return {"nudge": False}
    number = normalize(body.number)
    ev = db.get(CallEvent, body.call_id) if body.call_id else None
    if ev and ev.senior_id == senior.id:
        ev.duration_s = body.duration_s
        db.commit()
    notify_guardians(db, senior, "long_call", ref_id=ev.id if ev else None, number=number, minutes=body.duration_s // 60)
    return {"nudge": True, "speak": t("long_call.nudge", senior.language)}


# --------------------------------------------------------------- F3 help
@router.post("/help/pressed")
def help_pressed(user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    senior = _senior(user)
    alerts = notify_guardians(db, senior, "help_pressed")
    questions = ["stay_on_call", "secret", "pay", "authority", "app"]
    return {"guardians_alerted": len(alerts),
            "questions": [{"id": q, "text": t(f"check.q.{q}", senior.language)} for q in questions]}


class ChecklistBody(BaseModel):
    answers: dict[str, bool]


@router.post("/help/checklist")
def checklist(body: ChecklistBody, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    senior = _senior(user)
    yes = [q for q, v in body.answers.items() if v]
    if yes:
        detail = ", ".join(t(f"check.q.{q}", "en").rstrip("?") for q in yes if f"check.q.{q}" in T)
        notify_guardians(db, senior, "checklist_yes", detail=detail)
        guardians = [db.get(User, p.guardian_id) for p in db.scalars(
            select(Pairing).where(Pairing.senior_id == senior.id, Pairing.status == "active"))]
        return {"risk": True, "speak": t("check.stop", senior.language),
                "call_guardians": [{"name": g.name, "phone": g.phone} for g in guardians if g and not g.deleted_at],
                "helplines": _helplines(senior)}
    return {"risk": False, "speak": t("check.ok", senior.language)}


# ------------------------------------------------------------ F5 checker
class CheckBody(BaseModel):
    text: str


def run_check(db: Session, user: User | None, text: str, channel: str, lang: str,
              image: bytes | None = None, image_mime: str = "image/jpeg") -> tuple[MessageCheck, engine.MessageAssessment]:
    a = engine.assess_message(db, text, lang, image=image, image_mime=image_mime)
    mc = MessageCheck(user_id=user.id if user else None, channel=channel, content=(text or "[image]")[:4000],
                      verdict=a.verdict, category=a.category, reason=a.reason, engine=a.engine, confidence=a.confidence)
    db.add(mc)
    db.commit()
    if user and a.verdict == "scam" and user.role == "senior":
        notify_guardians(db, user, "message_scam", ref_id=mc.id, detail=reason(a.category, "en") if a.category else "")
    return mc, a


def format_verdict(a: engine.MessageAssessment, lang: str) -> str:
    return "\n".join([t(f"verdict.{a.verdict}", lang), t("verdict.why", lang, reason=a.reason), "", t("disclaimer", lang)])


@router.post("/check")
def check_message(body: CheckBody, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    mc, a = run_check(db, user, body.text, "app", user.language)
    return {"check_id": mc.id, "verdict": a.verdict, "category": a.category, "reason": a.reason,
            "engine": a.engine, "message": format_verdict(a, user.language)}


class Feedback(BaseModel):
    feedback: str  # correct | wrong


@router.post("/check/{check_id}/feedback")
def check_feedback(check_id: int, body: Feedback, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    mc = db.get(MessageCheck, check_id)
    if not mc or mc.user_id != user.id:
        raise HTTPException(404, "not found")
    mc.user_feedback = body.feedback
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------- number reports
class ReportBody(BaseModel):
    number: str
    label: str  # scam | genuine


def _report(db: Session, user: User, raw: str, label: str) -> None:
    number = normalize(raw)
    prior = db.scalar(select(NumberReport).where(NumberReport.number == number, NumberReport.reporter_id == user.id))
    row = db.get(ScamNumber, number) or ScamNumber(number=number, source="reports", category="user_report", scam_reports=0, genuine_reports=0)
    db.add(row)
    if prior:
        if prior.label == label:
            db.commit()
            return
        if prior.label == "scam":
            row.scam_reports = max(0, row.scam_reports - 1)
        else:
            row.genuine_reports = max(0, row.genuine_reports - 1)
        prior.label = label
    else:
        db.add(NumberReport(number=number, reporter_id=user.id, label=label))
    if label == "scam":
        row.scam_reports += 1
    else:
        row.genuine_reports += 1
    row.updated_at = now()
    db.commit()


@router.post("/reports")
def report_number(body: ReportBody, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    if body.label not in ("scam", "genuine"):
        raise HTTPException(422, "label must be scam or genuine")
    _report(db, user, body.number, body.label)
    return {"ok": True}


@router.get("/scam-numbers")
def scam_numbers(since: str | None = None, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    """Offline cache for the app, so screening works when the network is slow."""
    rows = db.scalars(select(ScamNumber)).all()
    out = [r.number for r in rows if engine.number_reputation(db, r.number)[0]]
    return {"numbers": out, "generated_at": now().isoformat()}


# -------------------------------------------------------- F7 report & recover
BANK_BLOCK_LINES = {
    # Placeholders - verify each number from the bank's official website before launch.
    "DEVBANK": {"name": "Dev Co-operative Bank", "block_line": "1800-000-0000"},
}


def _helplines(user: User) -> dict:
    bank = BANK_BLOCK_LINES.get(user.bank_code)
    return {
        "cyber_fraud_helpline": "1930",
        "cybercrime_portal": "https://cybercrime.gov.in",
        "chakshu": "https://sancharsaathi.gov.in/sfc/",
        "bank": bank,
    }


@router.get("/recover")
def recover(user: User = Depends(auth.current_user)):
    return {"helplines": _helplines(user),
            "steps": ["Call 1930 immediately - the first hour matters most.",
                      "Call your bank to block cards/UPI.",
                      "Report the number on Chakshu (Sanchar Saathi).",
                      "File a complaint at cybercrime.gov.in and keep screenshots."]}


# ----------------------------------------------------- F4 guardian inbox
@router.get("/alerts")
def list_alerts(user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Alert).where(Alert.guardian_id == user.id).order_by(Alert.id.desc()).limit(100)).all()
    out = []
    for a in rows:
        s = db.get(User, a.senior_id)
        out.append({"id": a.id, "kind": a.kind, "detail": a.detail, "ref_id": a.ref_id, "created_at": a.created_at.isoformat(),
                    "acknowledged": a.acknowledged_at is not None, "senior": {"name": s.name, "phone": s.phone}})
    return out


class AckBody(BaseModel):
    called_back: bool = False


@router.post("/alerts/{alert_id}/ack")
def ack_alert(alert_id: int, body: AckBody, user: User = Depends(auth.current_user), db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if not a or a.guardian_id != user.id:
        raise HTTPException(404, "not found")
    a.acknowledged_at = a.acknowledged_at or now()
    if body.called_back:
        a.called_back_at = a.called_back_at or now()
    db.commit()
    return {"ok": True}
