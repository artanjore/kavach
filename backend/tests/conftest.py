import os
import tempfile

_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_db.name}"
os.environ["KAVACH_ENV"] = "dev"
os.environ["KAVACH_LLM_ENABLED"] = "0"
os.environ["GUARDIAN_COOLOFF_HOURS"] = "24"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


_counter = [0]


def login(client, role="senior", name="", lang="hi"):
    _counter[0] += 1
    phone = f"98{_counter[0]:08d}"
    code = client.post("/v1/auth/otp/request", json={"phone": phone}).json()["dev_code"]
    r = client.post("/v1/auth/otp/verify", json={"phone": phone, "code": code, "role": role, "name": name, "language": lang})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}, r.json()["user"]


@pytest.fixture
def pair(client):
    """A senior paired with a WhatsApp-opted-in guardian."""
    s_h, s = login(client, "senior", "Kamla", "hi")
    g_h, g = login(client, "guardian", "Rohit", "en")
    client.post("/v1/consent", json={"purpose": "whatsapp_alerts", "granted": True}, headers=g_h)
    code = client.post("/v1/pairing/code", headers=s_h).json()["code"]
    p = client.post("/v1/pairing/join", json={"code": code}, headers=g_h).json()
    return {"s_h": s_h, "s": s, "g_h": g_h, "g": g, "pairing_id": p["id"]}
