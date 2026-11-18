"""The hosted demo's JavaScript engine must agree with the Python engine."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app.db import SessionLocal
from app.risk.engine import assess_message
from app.risk.phone import normalize, shape_signals
from app.risk.urls import url_signals
from scripts.build_static_demo import build, data

ROOT = Path(__file__).resolve().parent.parent
EXTRA = [
    "hi", "Your OTP is 123456. Do not share it with anyone.", "+44 7700 900123", "+91 90000 00001", "98765 43210",
    "http://45.12.88.10/itr-refund.apk", "https://www.onlinesbi.sbi/ login now", "https://incometax.gov.in refund",
    "Visit sbi-kyc-update.xyz today", "पैसा डबल करें, लॉटरी जीतें", "Mom I lost my phone, new number, send ₹5000",
    "Please install AnyDesk", "Pay customs duty fee for your parcel with drugs", "Meeting at 6 pm, bring the files",
]
NUMBERS = ["98765 43210", "+447700900123", "+91 12345", "1600123456", "", "09876543210", "+91 140 1234567", "0091 98765 43210"]
URLS = ["http://sbi-kyc-update.xyz/login", "https://bit.ly/abc", "http://xn--sb-ifa.com", "https://hdfc.bank.in", "http://1.2.3.4/x.apk", "https://www.rbi.org.in/x"]


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_js_engine_matches_python(tmp_path, client):  # client: app started, scam list seeded
    texts = [json.loads(l)["text"] for l in (ROOT / "data" / "message_eval.jsonl").read_text().splitlines() if l.strip()] + EXTRA
    cases = {"texts": texts, "numbers": NUMBERS, "urls": URLS}
    (tmp_path / "cases.json").write_text(json.dumps(cases, ensure_ascii=False))
    (tmp_path / "data.json").write_text(json.dumps(data(), ensure_ascii=False))
    runner = tmp_path / "run.cjs"
    runner.write_text(f"""
const fs = require('fs');
globalThis.KAVACH_DATA = JSON.parse(fs.readFileSync({json.dumps(str(tmp_path / 'data.json'))}, 'utf8'));
require({json.dumps(str(ROOT / 'app' / 'static' / 'standalone_engine.js'))});
const E = globalThis.KavachEngine;
const c = JSON.parse(fs.readFileSync({json.dumps(str(tmp_path / 'cases.json'))}, 'utf8'));
console.log(JSON.stringify({{
  texts: c.texts.map(t => {{ const a = E.assessMessage(t, 'hi'); return [a.verdict, a.reason_codes, a.reason]; }}),
  numbers: c.numbers.map(n => [E.normalize(n), E.shapeSignals(n)]),
  urls: c.urls.map(u => E.urlSignals(u)),
}}));
""")
    js = json.loads(subprocess.run(["node", str(runner)], capture_output=True, text=True, check=True).stdout)

    with SessionLocal() as db:
        for text, (verdict, codes, reason) in zip(texts, js["texts"]):
            py = assess_message(db, text, "hi", use_llm=False)
            assert (verdict, codes, reason) == (py.verdict, py.reason_codes, py.reason), text
    for n, (norm, shape) in zip(NUMBERS, js["numbers"]):
        assert norm == normalize(n) and shape == shape_signals(n), n
    for u, sig in zip(URLS, js["urls"]):
        assert sig == url_signals(u), u


def test_static_build_is_self_contained():
    html = build()
    assert html.startswith("<!doctype html>") and "window.KAVACH_DATA" in html and "KavachEngine" in html
    assert 'href="/bank"' not in html and "alert(" not in html and "confirm(" not in html
