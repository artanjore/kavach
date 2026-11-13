from datetime import timedelta

from app.db import SessionLocal
from app.models import OutboundMessage, Pairing, now
from tests.conftest import login


def _outbox_to(phone):
    with SessionLocal() as db:
        return db.query(OutboundMessage).filter(OutboundMessage.to == phone).all()


def test_otp_wrong_code_rejected(client):
    client.post("/v1/auth/otp/request", json={"phone": "9811111111"})
    assert client.post("/v1/auth/otp/verify", json={"phone": "9811111111", "code": "000000"}).status_code in (401,)


def test_pairing_and_permissions(client, pair):
    rows = client.get("/v1/pairing", headers=pair["s_h"]).json()
    assert rows[0]["guardian"]["name"] == "Rohit"
    assert rows[0]["permissions"]["see_message_checks"] is False  # off by default: dignity over surveillance
    # guardian cannot change permissions
    assert client.patch(f"/v1/pairing/{pair['pairing_id']}", json={"see_message_checks": True}, headers=pair["g_h"]).status_code == 404


def test_scam_call_warns_and_alerts_guardian(client, pair):
    r = client.post("/v1/calls/screen", json={"number": "9000000001"}, headers=pair["s_h"]).json()
    assert r["level"] == "warn" and "scam_list" in r["reasons"]
    assert "सावधान" in r["speak"]  # senior hears Hindi
    alerts = client.get("/v1/alerts", headers=pair["g_h"]).json()
    assert alerts[0]["kind"] == "call_warning"
    assert "looks like a scam" in alerts[0]["detail"]  # guardian reads English
    assert any("template" in m.body for m in _outbox_to(pair["g"]["phone"]))


def test_permission_off_means_no_alert(client, pair):
    client.patch(f"/v1/pairing/{pair['pairing_id']}", json={"see_call_warnings": False}, headers=pair["s_h"])
    client.post("/v1/calls/screen", json={"number": "9000000002"}, headers=pair["s_h"])
    assert client.get("/v1/alerts", headers=pair["g_h"]).json() == []


def test_unknown_and_repeat_calls(client, pair):
    r = client.post("/v1/calls/screen", json={"number": "9876500000"}, headers=pair["s_h"]).json()
    assert r["level"] == "safe"
    client.post("/v1/calls/screen", json={"number": "9876500000"}, headers=pair["s_h"])
    r = client.post("/v1/calls/screen", json={"number": "9876500000"}, headers=pair["s_h"]).json()
    assert r["level"] == "caution" and "repeat_unknown" in r["reasons"]


def test_user_reports_flip_number(client, pair):
    num = "9123400000"
    for _ in range(3):
        h, _u = login(client)
        client.post("/v1/reports", json={"number": num, "label": "scam"}, headers=h)
    r = client.post("/v1/calls/screen", json={"number": num}, headers=pair["s_h"]).json()
    assert r["level"] == "warn" and "user_reports" in r["reasons"]


def test_genuine_feedback(client, pair):
    r = client.post("/v1/calls/screen", json={"number": "+447700900999"}, headers=pair["s_h"]).json()
    assert r["level"] == "caution"
    assert client.post(f"/v1/calls/{r['call_id']}/outcome", json={"outcome": "genuine"}, headers=pair["s_h"]).status_code == 200


def test_help_flow(client, pair):
    r = client.post("/v1/help/pressed", headers=pair["s_h"]).json()
    assert r["guardians_alerted"] == 1 and len(r["questions"]) == 5
    r = client.post("/v1/help/checklist", json={"answers": {"stay_on_call": True, "secret": True, "pay": False}}, headers=pair["s_h"]).json()
    assert r["risk"] and r["call_guardians"][0]["name"] == "Rohit" and r["helplines"]["cyber_fraud_helpline"] == "1930"
    kinds = [a["kind"] for a in client.get("/v1/alerts", headers=pair["g_h"]).json()]
    assert kinds[:2] == ["checklist_yes", "help_pressed"]
    r = client.post("/v1/help/checklist", json={"answers": {"stay_on_call": False}}, headers=pair["s_h"]).json()
    assert r["risk"] is False


def test_long_call(client, pair):
    assert client.post("/v1/calls/long-call", json={"number": "9876511111", "duration_s": 120}, headers=pair["s_h"]).json()["nudge"] is False
    r = client.post("/v1/calls/long-call", json={"number": "9876511111", "duration_s": 900}, headers=pair["s_h"]).json()
    assert r["nudge"]
    assert "15 minutes" in client.get("/v1/alerts", headers=pair["g_h"]).json()[0]["detail"]


def test_message_check_in_app(client, pair):
    r = client.post("/v1/check", json={"text": "Your parcel with drugs was seized by customs, pay fee or face arrest"}, headers=pair["s_h"]).json()
    assert r["verdict"] == "scam" and "1930" in r["message"]


def test_whatsapp_webhook(client):
    assert client.get("/webhooks/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "dev-verify-token", "hub.challenge": "42"}).text == "42"
    payload = {"entry": [{"changes": [{"value": {"messages": [
        {"from": "919999900001", "type": "text", "text": {"body": "आपका केवाईसी अपडेट नहीं हुआ, खाता आज बंद होगा http://sbi-kyc.top"}}]}}]}]}
    assert client.post("/webhooks/whatsapp", json=payload).status_code == 200
    reply = _outbox_to("+919999900001")[-1].body
    assert "धोखाधड़ी" in reply  # Hindi verdict for Devanagari input
    payload["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = "hi"
    client.post("/webhooks/whatsapp", json=payload)
    assert "Kavach" in _outbox_to("+919999900001")[-1].body


def test_privacy_export_delete(client):
    h, _ = login(client)
    assert len(client.get("/v1/privacy/notice?lang=mr").json()["items"]) == 7
    client.post("/v1/check", json={"text": "hello"}, headers=h)
    assert len(client.get("/v1/me/export", headers=h).json()["message_checks"]) == 1
    assert client.delete("/v1/me", headers=h).json()["deleted"]
    assert client.get("/v1/me", headers=h).status_code == 401


def test_bank_hold_flow(client, pair):
    bank = {"X-API-Key": "dev-bank-key"}
    client.patch("/v1/me", json={"bank_code": "DEVBANK", "bank_customer_ref": "CUST-1"}, headers=pair["s_h"])
    ev = {"event_id": "E1", "customer_ref": "CUST-1", "amount_paise": 75_000_00, "payee_label": "Unknown Traders", "first_time_payee": True}

    # No trusted person yet
    assert client.post("/v1/bank/risk-events", json=ev, headers=bank).json()["status"] == "no_trusted_person"

    # Senior grants approval rights; still not effective during the 24h cooling-off
    client.patch(f"/v1/pairing/{pair['pairing_id']}", json={"approve_transfers": True}, headers=pair["s_h"])
    ev["event_id"] = "E2"
    assert client.post("/v1/bank/risk-events", json=ev, headers=bank).json()["status"] == "no_trusted_person"

    # Fast-forward past cooling-off
    with SessionLocal() as db:
        p = db.get(Pairing, pair["pairing_id"])
        p.approve_transfers_effective_at = now() - timedelta(minutes=1)
        db.commit()
    ev["event_id"] = "E3"
    hold = client.post("/v1/bank/risk-events", json=ev, headers=bank).json()
    assert hold["status"] == "pending"
    assert client.post("/v1/bank/risk-events", json=ev, headers=bank).json()["hold_id"] == hold["hold_id"]  # idempotent

    alert = client.get("/v1/alerts", headers=pair["g_h"]).json()[0]
    assert alert["kind"] == "transfer_hold" and "75,000" in alert["detail"]

    # A stranger cannot decide
    other_h, _ = login(client, "guardian")
    assert client.post(f"/v1/holds/{hold['hold_id']}/decision", json={"decision": "approve"}, headers=other_h).status_code == 403

    r = client.post(f"/v1/holds/{hold['hold_id']}/decision", json={"decision": "decline"}, headers=pair["g_h"]).json()
    assert r["status"] == "declined"
    assert client.get("/v1/bank/holds/E3", headers=bank).json()["status"] == "declined"
    assert client.post(f"/v1/holds/{hold['hold_id']}/decision", json={"decision": "approve"}, headers=pair["g_h"]).status_code == 409

    dash = client.get("/v1/bank/dashboard", headers=bank).json()
    assert dash["holds_by_status"]["declined"] == 1 and dash["declined_amount_rupees"] == 75000

    # Senior removes the guardian -> immediately loses approval power
    client.delete(f"/v1/pairing/{pair['pairing_id']}", headers=pair["s_h"])
    ev["event_id"] = "E4"
    assert client.post("/v1/bank/risk-events", json=ev, headers=bank).json()["status"] == "no_trusted_person"


def test_hold_expiry(client, pair):
    bank = {"X-API-Key": "dev-bank-key"}
    client.patch("/v1/me", json={"bank_code": "DEVBANK", "bank_customer_ref": "CUST-EXP"}, headers=pair["s_h"])
    client.patch(f"/v1/pairing/{pair['pairing_id']}", json={"approve_transfers": True}, headers=pair["s_h"])
    with SessionLocal() as db:
        db.get(Pairing, pair["pairing_id"]).approve_transfers_effective_at = now() - timedelta(minutes=1)
        db.commit()
    hold = client.post("/v1/bank/risk-events", json={"event_id": "X1", "customer_ref": "CUST-EXP", "amount_paise": 2_000_000}, headers=bank).json()
    from app.models import TransferHold
    with SessionLocal() as db:
        db.get(TransferHold, hold["hold_id"]).expires_at = now() - timedelta(seconds=1)
        db.commit()
    assert client.get("/v1/bank/holds/X1", headers=bank).json()["status"] == "expired"


def test_bank_auth_and_metrics(client):
    assert client.get("/v1/bank/dashboard", headers={"X-API-Key": "nope"}).status_code == 401
    m = client.get("/v1/admin/metrics", headers={"X-Admin-Token": "dev-admin"}).json()
    assert m["activated_pairs"] >= 1


def test_qr_and_join_page(client, pair):
    c = client.post("/v1/pairing/code", headers=pair["s_h"]).json()
    assert c["join_url"].endswith(f"/join?code={c['code']}")
    r = client.get(f"/v1/pairing/qr.png?code={c['code']}", headers=pair["s_h"])
    assert r.status_code == 200 and r.content[:4] == b"\x89PNG"
    assert client.get(f"/v1/pairing/qr.png?code={c['code']}", headers=pair["g_h"]).status_code == 404  # not their code
    page = client.get(f"/join?code={c['code']}").text
    assert f"kavach://join?code={c['code']}" in page
    assert "<script" not in client.get("/join?code=<script>alert(1)</script>").text


def test_demo_setup_and_pages(client):
    d = client.post("/v1/demo/setup?senior_lang=mr").json()
    s_h = {"Authorization": f"Bearer {d['senior']['token']}"}
    r = client.post("/v1/calls/screen", json={"number": "+919000000001"}, headers=s_h).json()
    assert r["level"] == "warn" and "सावध" in r["speak"]
    assert client.get(f"/v1/demo/outbox?to=%2B{d['guardian']['phone'][1:]}").json()[0]["channel"] == "whatsapp"
    hold = client.post("/v1/bank/risk-events", headers={"X-API-Key": d["bank"]["api_key"]},
                       json={"event_id": "DEMO-1", "customer_ref": d["senior"]["customer_ref"], "amount_paise": 6_000_000}).json()
    assert hold["status"] == "pending"  # demo pair skips the cooling-off
    assert "Kavach" in client.get("/demo").text and "Bank partner console" in client.get("/bank").text
