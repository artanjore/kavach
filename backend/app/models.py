"""Database schema.

Data-minimisation rule (see docs/PRIVACY.md): we store caller numbers only for
calls we flagged, messages only when the user forwarded them to us, and never
call audio, SMS, contacts or bank credentials.
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80), default="")
    role: Mapped[str] = mapped_column(String(10), default="senior")  # senior | guardian
    language: Mapped[str] = mapped_column(String(5), default="hi")
    whatsapp_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    bank_code: Mapped[str] = mapped_column(String(20), default="")  # senior's bank, for F7 and v2
    bank_customer_ref: Mapped[str] = mapped_column(String(64), default="", index=True)
    push_token: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuthToken(Base):
    __tablename__ = "auth_tokens"
    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class OtpCode(Base):
    __tablename__ = "otp_codes"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class Pairing(Base):
    """A senior–guardian link. The senior controls every permission."""
    __tablename__ = "pairings"
    __table_args__ = (UniqueConstraint("senior_id", "guardian_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    senior_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    guardian_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(10), default="active")  # active | revoked
    see_call_warnings: Mapped[bool] = mapped_column(Boolean, default=True)
    see_help_presses: Mapped[bool] = mapped_column(Boolean, default=True)
    see_message_checks: Mapped[bool] = mapped_column(Boolean, default=False)
    approve_transfers: Mapped[bool] = mapped_column(Boolean, default=False)
    # Transfer-approval power only takes effect after a cooling-off period, so a
    # newly added (possibly abusive) guardian cannot immediately control money.
    approve_transfers_effective_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    senior: Mapped[User] = relationship(foreign_keys=[senior_id])
    guardian: Mapped[User] = relationship(foreign_keys=[guardian_id])


class PairingCode(Base):
    __tablename__ = "pairing_codes"
    code: Mapped[str] = mapped_column(String(6), primary_key=True)
    senior_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class ScamNumber(Base):
    __tablename__ = "scam_numbers"
    number: Mapped[str] = mapped_column(String(20), primary_key=True)
    category: Mapped[str] = mapped_column(String(40), default="")
    source: Mapped[str] = mapped_column(String(20), default="seed")  # seed | reports | partner
    scam_reports: Mapped[int] = mapped_column(Integer, default=0)
    genuine_reports: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class NumberReport(Base):
    __tablename__ = "number_reports"
    __table_args__ = (UniqueConstraint("number", "reporter_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20), index=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    label: Mapped[str] = mapped_column(String(10))  # scam | genuine
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class CallEvent(Base):
    """Only written for calls we screened from unknown numbers."""
    __tablename__ = "call_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    senior_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    number: Mapped[str] = mapped_column(String(20), index=True)
    level: Mapped[str] = mapped_column(String(10))  # safe | caution | warn
    reason_code: Mapped[str] = mapped_column(String(40), default="")
    duration_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    outcome: Mapped[str] = mapped_column(String(10), default="")  # "" | genuine | scam
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class MessageCheck(Base):
    __tablename__ = "message_checks"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(10))  # app | whatsapp
    content: Mapped[str] = mapped_column(Text)
    verdict: Mapped[str] = mapped_column(String(12))  # safe | suspicious | scam
    category: Mapped[str] = mapped_column(String(40), default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    engine: Mapped[str] = mapped_column(String(10))  # rules | llm
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    user_feedback: Mapped[str] = mapped_column(String(10), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    senior_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    guardian_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # call_warning | help_pressed | checklist_yes | message_scam | long_call | transfer_hold
    detail: Mapped[str] = mapped_column(Text, default="")
    ref_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    called_back_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class OutboundMessage(Base):
    """Every WhatsApp/push we send (or would send in dev). Doubles as an audit trail."""
    __tablename__ = "outbox"
    id: Mapped[int] = mapped_column(primary_key=True)
    channel: Mapped[str] = mapped_column(String(10))  # whatsapp | push
    to: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), default="queued")  # queued | sent | failed | dev
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class ConsentRecord(Base):
    """DPDP: an append-only record of each consent given or withdrawn."""
    __tablename__ = "consents"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(40))
    granted: Mapped[bool] = mapped_column(Boolean)
    notice_version: Mapped[str] = mapped_column(String(20))
    language: Mapped[str] = mapped_column(String(5))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class TransferHold(Base):
    """v2: a bank tells us it has paused a transfer; a guardian approves or declines.

    We never move or hold money. The bank holds; we carry the decision.
    """
    __tablename__ = "transfer_holds"
    __table_args__ = (UniqueConstraint("bank_code", "bank_event_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    bank_code: Mapped[str] = mapped_column(String(20), index=True)
    bank_event_id: Mapped[str] = mapped_column(String(64))
    senior_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount_paise: Mapped[int] = mapped_column(Integer)
    payee_label: Mapped[str] = mapped_column(String(120), default="")
    first_time_payee: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(10), default="pending")  # pending | approved | declined | expired
    decided_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decision_note: Mapped[str] = mapped_column(Text, default="")
    callback_url: Mapped[str] = mapped_column(String(255), default="")
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(40))  # user:12 | bank:DEVBANK | system
    action: Mapped[str] = mapped_column(String(40))
    target: Mapped[str] = mapped_column(String(60), default="")
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
