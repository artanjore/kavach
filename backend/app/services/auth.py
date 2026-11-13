"""Phone-OTP login and bearer tokens.

In dev the OTP is returned in the API response. In production plug an SMS
provider into send_otp_sms() (e.g. MSG91, Gupshup); DLT template registration
with your telecom operator is required for SMS in India.
"""
import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import AuthToken, OtpCode, User, now

log = logging.getLogger(__name__)
OTP_TTL = timedelta(minutes=10)
MAX_ATTEMPTS = 5


def _hash(code: str, phone: str) -> str:
    return hashlib.sha256(f"{phone}:{code}".encode()).hexdigest()


def send_otp_sms(phone: str, code: str) -> None:
    log.info("OTP for %s: %s (SMS provider not configured)", phone[-4:], "****" if not settings.is_dev else code)


def request_otp(db: Session, phone: str) -> str:
    code = f"{secrets.randbelow(10**6):06d}"
    db.add(OtpCode(phone=phone, code_hash=_hash(code, phone), expires_at=now() + OTP_TTL))
    db.commit()
    send_otp_sms(phone, code)
    return code


def verify_otp(db: Session, phone: str, code: str) -> bool:
    otp = db.scalars(
        select(OtpCode).where(OtpCode.phone == phone, OtpCode.used.is_(False)).order_by(OtpCode.id.desc())
    ).first()
    if not otp or otp.expires_at < now() or otp.attempts >= MAX_ATTEMPTS:
        return False
    otp.attempts += 1
    ok = hmac.compare_digest(otp.code_hash, _hash(code, phone))
    if ok:
        otp.used = True
    db.commit()
    return ok


def issue_token(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.add(AuthToken(token=token, user_id=user.id))
    db.commit()
    return token


def current_user(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> User:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401, "missing bearer token")
    row = db.get(AuthToken, token)
    user = db.get(User, row.user_id) if row else None
    if not user or user.deleted_at:
        raise HTTPException(401, "invalid token")
    return user


def bank_caller(x_api_key: str = Header(default="")) -> str:
    code = settings.bank_keys().get(x_api_key)
    if not code:
        raise HTTPException(401, "invalid bank api key")
    return code
