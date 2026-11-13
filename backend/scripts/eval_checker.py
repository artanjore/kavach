"""Measure the message checker against data/message_eval.jsonl.

    python scripts/eval_checker.py            # rules only (free, offline)
    python scripts/eval_checker.py --llm      # rules + LLM (needs ANTHROPIC_API_KEY; costs money)

Grow the eval set every week from real forwarded messages (with consent), and
re-run before changing rules, prompts or the model.
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.risk.engine import assess_message  # noqa: E402

use_llm = "--llm" in sys.argv
rows = [json.loads(l) for l in (Path(__file__).resolve().parent.parent / "data" / "message_eval.jsonl").read_text().splitlines() if l.strip()]
confusion = Counter()
misses = []
for r in rows:
    a = assess_message(None, r["text"], "en", use_llm=use_llm)
    confusion[(r["label"], a.verdict)] += 1
    if a.verdict != r["label"]:
        misses.append((r["label"], a.verdict, a.reason_codes, r["text"][:80]))

labels = ["scam", "suspicious", "safe"]
print(f"{'truth/pred':<12}" + "".join(f"{p:>12}" for p in labels))
for t in labels:
    print(f"{t:<12}" + "".join(f"{confusion[(t, p)]:>12}" for p in labels))
exact = sum(confusion[(l, l)] for l in labels) / len(rows)
scams = [r for r in rows if r["label"] == "scam"]
scam_caught = sum(confusion[("scam", p)] for p in ("scam", "suspicious")) / len(scams)
safe_n = sum(1 for r in rows if r["label"] == "safe")
false_alarm = sum(confusion[("safe", p)] for p in ("scam", "suspicious")) / safe_n
print(f"\nexact accuracy {exact:.0%} | scams flagged (scam or suspicious) {scam_caught:.0%} | safe messages wrongly flagged {false_alarm:.0%}")
if misses:
    print("\nmisses:")
    for m in misses:
        print(" ", m)
