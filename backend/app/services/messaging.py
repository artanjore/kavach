"""Outbound WhatsApp (Cloud API) and push.

Every message goes through the outbox table first. In dev, or when WhatsApp
credentials are missing, messages stay in the outbox with status "dev" so the
whole flow can be tested without Meta access.

Guardian alerts are business-initiated, so they MUST use an approved utility
template (WHATSAPP_ALERT_TEMPLATE, one body parameter {{1}} = alert text) and
the guardian must have opted in. Replies to a user who messaged us in the last
24 hours can be free-form text.
"""
import logging

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..models import OutboundMessage

log = logging.getLogger(__name__)


def _wa_url() -> str:
    return f"https://graph.facebook.com/{settings.wa_graph_version}/{settings.wa_phone_number_id}/messages"


def _wa_live() -> bool:
    return bool(settings.wa_token and settings.wa_phone_number_id) and not settings.is_dev


def _post(payload: dict) -> tuple[str, str]:
    try:
        r = httpx.post(_wa_url(), json=payload, headers={"Authorization": f"Bearer {settings.wa_token}"}, timeout=10)
        if r.status_code >= 300:
            return "failed", r.text[:500]
        return "sent", ""
    except httpx.HTTPError as e:
        return "failed", str(e)[:500]


def send_whatsapp_text(db: Session, to: str, body: str) -> OutboundMessage:
    msg = OutboundMessage(channel="whatsapp", to=to, body=body)
    if _wa_live():
        msg.status, msg.error = _post({"messaging_product": "whatsapp", "to": to.lstrip("+"), "type": "text", "text": {"body": body[:4096]}})
    else:
        msg.status = "dev"
    db.add(msg)
    db.commit()
    return msg


def send_whatsapp_alert(db: Session, to: str, body: str, lang: str) -> OutboundMessage:
    msg = OutboundMessage(channel="whatsapp", to=to, body=f"[template:{settings.wa_alert_template}] {body}")
    if _wa_live():
        lang_code = {"hi": "hi", "mr": "mr", "en": "en"}.get(lang, "en")
        msg.status, msg.error = _post({
            "messaging_product": "whatsapp", "to": to.lstrip("+"), "type": "template",
            "template": {"name": settings.wa_alert_template, "language": {"code": lang_code},
                         "components": [{"type": "body", "parameters": [{"type": "text", "text": body[:1000]}]}]},
        })
    else:
        msg.status = "dev"
    db.add(msg)
    db.commit()
    return msg


def send_push(db: Session, token: str, title: str, body: str, data: dict | None = None) -> OutboundMessage:
    """Push via FCM. Wire up firebase-admin here once a Firebase project exists."""
    msg = OutboundMessage(channel="push", to=token or "(no token)", body=f"{title}: {body}", status="dev")
    db.add(msg)
    db.commit()
    return msg


def download_whatsapp_media(media_id: str) -> tuple[bytes, str] | None:
    if not settings.wa_token:
        return None
    try:
        h = {"Authorization": f"Bearer {settings.wa_token}"}
        meta = httpx.get(f"https://graph.facebook.com/{settings.wa_graph_version}/{media_id}", headers=h, timeout=10).json()
        r = httpx.get(meta["url"], headers=h, timeout=20)
        r.raise_for_status()
        return r.content, meta.get("mime_type", "image/jpeg")
    except (httpx.HTTPError, KeyError, ValueError) as e:
        log.error("media download failed: %s", e)
        return None
