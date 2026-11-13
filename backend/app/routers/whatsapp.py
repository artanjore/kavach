"""F5 over WhatsApp: users forward a message, link, number or screenshot; we reply.

Meta webhook setup: callback URL = https://<host>/webhooks/whatsapp,
verify token = WHATSAPP_VERIFY_TOKEN, subscribe to the "messages" field.
"""
import hashlib
import hmac
import json
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import User
from ..services import messaging
from ..services.i18n import t
from .protect import format_verdict, run_check

router = APIRouter(tags=["whatsapp"])
log = logging.getLogger(__name__)
GREETINGS = re.compile(r"^\s*(hi|hello|hey|namaste|namaskar|start|नमस्ते|नमस्कार)\s*[!.]*\s*$", re.IGNORECASE)
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
MARATHI_HINTS = re.compile(r"(आहे|नाही|तुम्ही|आम्ही|करा|झाले)")


@router.get("/webhooks/whatsapp")
def verify(request: Request):
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == settings.wa_verify_token:
        return Response(q.get("hub.challenge", ""), media_type="text/plain")
    raise HTTPException(403, "verification failed")


def _guess_lang(text: str, user: User | None) -> str:
    if user:
        return user.language
    if DEVANAGARI.search(text or ""):
        return "mr" if MARATHI_HINTS.search(text) else "hi"
    return "en"


@router.post("/webhooks/whatsapp")
async def receive(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    if settings.wa_app_secret:
        sig = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(settings.wa_app_secret.encode(), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise HTTPException(403, "bad signature")
    try:
        payload = json.loads(raw or b"{}")
    except ValueError:
        raise HTTPException(400, "bad json")

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []) or []:
                try:
                    handle_message(db, msg)
                except Exception:  # never fail the webhook: Meta retries and duplicates replies
                    log.exception("failed to handle WhatsApp message")
    return {"ok": True}


def handle_message(db: Session, msg: dict) -> None:
    sender = "+" + msg.get("from", "").lstrip("+")
    user = db.scalar(select(User).where(User.phone == sender, User.deleted_at.is_(None)))
    kind = msg.get("type")
    text, image, mime = "", None, "image/jpeg"

    if kind == "text":
        text = msg.get("text", {}).get("body", "")
    elif kind == "image":
        text = msg.get("image", {}).get("caption", "")
        media = messaging.download_whatsapp_media(msg["image"]["id"])
        if media:
            image, mime = media
    elif kind == "contacts":
        phones = [p.get("phone", "") for c in msg.get("contacts", []) for p in c.get("phones", [])]
        text = " ".join(phones)
    else:
        lang = _guess_lang("", user)
        messaging.send_whatsapp_text(db, sender, t("wa.unsupported", lang))
        return

    lang = _guess_lang(text, user)
    if GREETINGS.match(text or "") and not image:
        messaging.send_whatsapp_text(db, sender, t("wa.welcome", lang))
        return
    if not text and not image:
        messaging.send_whatsapp_text(db, sender, t("wa.unsupported", lang))
        return

    _, a = run_check(db, user, text, "whatsapp", lang, image=image, image_mime=mime)
    messaging.send_whatsapp_text(db, sender, format_verdict(a, lang))
