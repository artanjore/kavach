"""LLM path with a fake client: checks request shape, parsing and merge rules (no network)."""
import json
from types import SimpleNamespace

from app.risk import engine, llm


class FakeMessages:
    def __init__(self, out, stop="end_turn"):
        self.out, self.stop, self.kwargs = out, stop, None

    def create(self, **kw):
        self.kwargs = kw
        return SimpleNamespace(stop_reason=self.stop, content=[SimpleNamespace(type="text", text=json.dumps(self.out))])


def _install(monkeypatch, out, stop="end_turn"):
    fake = FakeMessages(out, stop)
    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(llm, "_get_client", lambda: SimpleNamespace(beta=SimpleNamespace(messages=fake)))
    return fake


def test_llm_settles_ambiguous(monkeypatch):
    fake = _install(monkeypatch, {"verdict": "scam", "category": "other", "confidence": 0.9,
                                  "reason_en": "A stranger wants money.", "reason_local": "अनजान व्यक्ति पैसे माँग रहा है।"})
    a = engine.assess_message(None, "Hello madam, small verification needed, please call me back", "hi")
    assert a.engine == "llm" and a.verdict == "scam" and "पैसे" in a.reason
    assert fake.kwargs["output_config"]["format"]["type"] == "json_schema"
    assert fake.kwargs["fallbacks"] == "default"
    assert "<forwarded_content>" in fake.kwargs["messages"][0]["content"][-1]["text"]


def test_llm_cannot_downgrade_rules_scam(monkeypatch):
    _install(monkeypatch, {"verdict": "safe", "category": "none", "confidence": 0.8, "reason_en": "ok", "reason_local": "ok"})
    a = engine.assess_message(None, "Install AnyDesk now", "en")  # rules: scam (score 6, not decisive)
    assert a.verdict == "scam"


def test_llm_refusal_falls_back_to_rules(monkeypatch):
    _install(monkeypatch, {}, stop="refusal")
    a = engine.assess_message(None, "Hello, how are you?", "en")
    assert a.engine == "rules" and a.verdict == "safe"


def test_screenshot_goes_to_llm(monkeypatch):
    fake = _install(monkeypatch, {"verdict": "suspicious", "category": "other", "confidence": 0.5, "reason_en": "x", "reason_local": "x"})
    engine.assess_message(None, "", "en", image=b"\x89PNG", image_mime="image/png")
    assert fake.kwargs["messages"][0]["content"][0]["type"] == "image"
