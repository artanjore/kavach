"""Risk engine v1: rules first, LLM second.

Two entry points:
- assess_call(): F2 pre-answer warning. Must answer in well under a second,
  so it is rules-only (scam list, user reports, number shape, repeat calls).
- assess_message(): F5 checker. Rules on text/URLs/numbers, then an LLM second
  opinion when rules are not decisive (or for screenshots).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import CallEvent, ScamNumber, now
from ..services.i18n import reason as reason_text
from . import llm
from .patterns import CATEGORIES, PHONE_RE, URL_RE
from .phone import normalize, shape_signals
from .urls import URL_SIGNAL_WEIGHTS, url_signals

LEVEL_ORDER = {"safe": 0, "caution": 1, "warn": 2}
VERDICT_ORDER = {"safe": 0, "suspicious": 1, "scam": 2}


# ---------------------------------------------------------------- calls (F2)
@dataclass
class CallAssessment:
    number: str
    level: str  # safe | caution | warn
    reasons: list[str] = field(default_factory=list)


def number_reputation(db: Session, number: str) -> tuple[bool, list[str]]:
    """Returns (is_scam, reason_codes) from our list and user reports."""
    row = db.get(ScamNumber, number)
    if not row:
        return False, []
    net_reports = row.scam_reports - row.genuine_reports
    if row.source in ("seed", "partner") and row.genuine_reports < settings.report_threshold:
        return True, ["scam_list"]
    if net_reports >= settings.report_threshold:
        return True, ["user_reports"]
    return False, []


def assess_call(db: Session, senior_id: int, raw_number: str) -> CallAssessment:
    number = normalize(raw_number)
    is_scam, reasons = number_reputation(db, number)
    if is_scam:
        return CallAssessment(number, "warn", reasons)

    shape = shape_signals(raw_number)
    if "trai_1600_series" in shape:
        return CallAssessment(number, "safe", [])

    caution = [s for s in shape if s in ("international", "malformed_indian", "hidden_number")]

    since = now() - timedelta(hours=24)
    recent = db.scalar(
        select(func.count()).select_from(CallEvent).where(
            CallEvent.senior_id == senior_id, CallEvent.number == number, CallEvent.created_at >= since
        )
    ) or 0
    if recent + 1 >= settings.repeat_call_threshold:
        caution.append("repeat_unknown")

    if "malformed_indian" in caution and ("international" in caution or "repeat_unknown" in caution):
        return CallAssessment(number, "warn", caution)
    if caution:
        return CallAssessment(number, "caution", caution)
    return CallAssessment(number, "safe", [])


# ------------------------------------------------------------- messages (F5)
@dataclass
class MessageAssessment:
    verdict: str  # safe | suspicious | scam
    category: str
    reason_codes: list[str]
    reason: str  # in the user's language
    engine: str  # rules | llm
    confidence: float
    numbers: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)


def rules_score(text: str, db: Session | None = None) -> tuple[int, list[str], list[str], list[str]]:
    score = 0
    codes: list[str] = []
    for cat in CATEGORIES:
        if cat.matches(text):
            score += cat.weight
            codes.append(cat.key)

    urls = [u.rstrip(".,)") for u in URL_RE.findall(text)]
    for u in urls:
        for sig in url_signals(u):
            score += URL_SIGNAL_WEIGHTS.get(sig, 0)
            if sig != "official_domain" and sig not in codes:
                codes.append(sig)

    numbers = []
    for m in PHONE_RE.findall(text):
        n = normalize(m)
        if len(n.lstrip("+")) >= 10:
            numbers.append(n)
            if db is not None:
                is_scam, r = number_reputation(db, n)
                if is_scam:
                    score += 5
                    codes.extend(c for c in r if c not in codes)
    return score, codes, urls, numbers


def _verdict_from_score(score: int) -> str:
    if score >= 6:
        return "scam"
    if score >= 3:
        return "suspicious"
    return "safe"


def assess_message(db: Session | None, text: str, lang: str, image: bytes | None = None, image_mime: str = "image/jpeg",
                   use_llm: bool = True) -> MessageAssessment:
    text = (text or "").strip()
    score, codes, urls, numbers = rules_score(text, db) if text else (0, [], [], [])

    # A bare phone number: answer from reputation and shape only.
    if text and not urls and numbers and len(PHONE_RE.sub("", text).strip()) < 4:
        n = numbers[0]
        if "scam_list" in codes or "user_reports" in codes:
            verdict = "scam"
        else:
            shape = shape_signals(n)
            codes = [s for s in shape if s in ("international", "malformed_indian")]
            verdict = "suspicious" if codes else "safe"
        primary = codes[0] if codes else "no_signals"
        return MessageAssessment(verdict, primary, codes, reason_text(primary, lang), "rules", 0.6, numbers, urls)

    rules_verdict = _verdict_from_score(score)
    primary = codes[0] if codes else "no_signals"
    result = MessageAssessment(rules_verdict, primary if codes else "none", codes,
                               _join_reasons(codes, lang) if codes else reason_text("no_signals", lang),
                               "rules", min(1.0, 0.4 + score / 15), numbers, urls)

    # Rules are decisive for a strong scam signal. Otherwise ask the LLM.
    decisive = score >= 9 and not image
    if use_llm and not decisive and llm.available():
        v = llm.classify(text, lang, image=image, image_mime=image_mime)
        if v is not None:
            # Never let the LLM downgrade a rules "scam"; let it upgrade or settle ambiguity.
            if VERDICT_ORDER[v.verdict] >= VERDICT_ORDER[rules_verdict] or rules_verdict == "suspicious":
                final = v.verdict if rules_verdict != "scam" else "scam"
                result = MessageAssessment(final, v.category, codes, v.reason_local or v.reason_en, "llm", v.confidence, numbers, urls)
    return result


def _join_reasons(codes: list[str], lang: str) -> str:
    parts = [reason_text(c, lang) for c in codes[:2]]
    sep = {"en": "; ", "hi": "; ", "mr": "; "}.get(lang, "; ")
    return sep.join(parts)
