"""Build the hosted demo: one self-contained HTML page with no server.

    python scripts/build_static_demo.py      -> ../docs/demo/index.html

Takes app/static/demo.html (the same UI as the local /demo page), and injects
  1. KAVACH_DATA: scam patterns, weights, URL lists, en/hi/mr text and seed numbers
     exported from the Python code (so the two never drift apart), and
  2. app/static/standalone_engine.js: the risk engine and API routes ported to JS.
The result also works on GitHub Pages or as a claude.ai artifact.
"""
import io
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("KAVACH_ENV", "dev")
os.environ.setdefault("DATABASE_URL", "sqlite://")

import segno  # noqa: E402

from app.config import settings  # noqa: E402
from app.risk import patterns, urls  # noqa: E402
from app.risk.phone import normalize  # noqa: E402
from app.routers.protect import BANK_BLOCK_LINES, recover  # noqa: E402
from app.services.i18n import REASONS, T  # noqa: E402

DEMO_CODE = "482913"
DEMO_JOIN = f"kavach://join?code={DEMO_CODE}"


def qr_svg(data: str) -> str:
    buf = io.BytesIO()
    segno.make(data, error="m").save(buf, kind="svg", scale=8, border=2, xmldecl=False, svgns=True)
    return buf.getvalue().decode()


def data() -> dict:
    seed = json.loads((ROOT / "data" / "scam_numbers_seed.json").read_text())["numbers"]
    return {
        "CATEGORIES": [{"key": c.key, "weight": c.weight, "patterns": [p.pattern for p in c.patterns],
                        "negatives": [n.pattern for n in c.negatives]} for c in patterns.CATEGORIES],
        "URL_RE": patterns.URL_RE.pattern,
        "PHONE_RE": patterns.PHONE_RE.pattern,
        "URLS": {"shorteners": sorted(urls.SHORTENERS), "risky_tlds": sorted(urls.RISKY_TLDS),
                 "brands": {k: sorted(v) for k, v in urls.BRANDS.items()}, "official_suffixes": list(urls.OFFICIAL_SUFFIXES),
                 "weights": urls.URL_SIGNAL_WEIGHTS},
        "T": T,
        "REASONS": REASONS,
        "SEED_NUMBERS": [{"number": normalize(n["number"]), "category": n.get("category", "")} for n in seed],
        "SETTINGS": {"report_threshold": settings.report_threshold, "repeat_call_threshold": settings.repeat_call_threshold,
                     "long_call_seconds": settings.long_call_seconds, "hold_decision_minutes": settings.hold_decision_minutes,
                     "guardian_cooloff_hours": settings.guardian_approval_cooloff_hours},
        "BANK_BLOCK_LINES": BANK_BLOCK_LINES,
        "RECOVER_STEPS": recover(SimpleNamespace(bank_code=""))["steps"],
        "DEMO_QR": {"code": DEMO_CODE, "join_url": DEMO_JOIN, "svg": qr_svg(DEMO_JOIN)},
    }


def replace_once(s: str, old: str, new: str) -> str:
    assert s.count(old) == 1, f"expected exactly one {old[:60]!r}"
    return s.replace(old, new)


def build() -> str:
    html = (ROOT / "app" / "static" / "demo.html").read_text()
    engine = (ROOT / "app" / "static" / "standalone_engine.js").read_text()
    payload = json.dumps(data(), ensure_ascii=False).replace("</", "<\\/")
    html = replace_once(html, "Every button calls the real backend. Nothing on this page is mocked.",
                        "Runs entirely in your browser with the same scam rules as the real backend. Demo data only: no real calls, messages or money.")
    html = replace_once(html, '<a class="hbtn" href="/bank" target="_blank" style="flex:0 0 auto;text-decoration:none;color:inherit">Open full console ↗</a>', "")
    html = replace_once(html, '<p class="label" style="margin:.8rem 1rem .3rem">API calls</p>',
                        '<p class="label" style="margin:.8rem 1rem .3rem">API calls (simulated in your browser)</p>')
    html = replace_once(html, "\n<script>\n\"use strict\";",
                        f"\n<script>window.KAVACH_DATA = {payload};</script>\n<script>\n{engine}\n</script>\n<script>\n\"use strict\";")
    # Open straight into a ready demo.
    html = replace_once(html, "setInterval(() => { guardianRefresh();",
                        "start().catch((e) => notice(e.message));\nsetInterval(() => { guardianRefresh();")
    return html


if __name__ == "__main__":
    out = ROOT.parent / "docs" / "demo" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build())
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
