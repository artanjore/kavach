# Kavach (working name): scam protection for Indian seniors

The MVP from the PRD: an Android app for the senior, a guardian (family) mode,
a WhatsApp scam checker, and the v2 bank "trusted person" API. One backend.

```
kavach/
├── backend/            FastAPI + SQLAlchemy (SQLite in dev, Postgres in prod)
│   ├── app/risk/       risk engine: number rules, message/URL rules, LLM second opinion
│   ├── app/routers/    users+pairing+consent, protect (F2–F7), whatsapp, bank (F9/F11), admin metrics
│   ├── app/services/   auth (OTP), alerts fan-out, WhatsApp/push outbox, i18n (en/hi/mr), privacy notice
│   ├── data/           seed scam numbers (placeholders) + labelled message eval set
│   ├── scripts/        eval_checker.py
│   └── tests/          25 tests
├── android/            Kotlin app, framework APIs only (no third-party libraries)
└── docs/               BANK_API.md, PLAY_POLICY.md, PRIVACY.md
```

## Feature status

| PRD | Feature | Backend | Android | Notes |
|---|---|---|---|---|
| F1 | Paired onboarding | ✅ OTP login, 6-digit pairing code, senior-controlled permissions, consent log | ✅ language → role → OTP → notice read aloud → call-screening role → pairing code | QR code not done (code is typed); SMS provider not wired (dev returns OTP) |
| F2 | Pre-answer call warning | ✅ scam list, ≥3 user reports, number shape (+91 spoofing, international, 1600-series), repeat calls | ✅ `CallScreeningService` + full-screen warning + spoken in her language + offline scam-list cache | Never blocks a call; warns only |
| F3 | "Am I being scammed?" | ✅ alerts guardian on press; 5-question checklist; any "yes" → stop screen | ✅ big button, spoken questions, home-screen widget, works offline with family numbers | |
| F4 | Guardian alerts | ✅ WhatsApp template + push hook + in-app inbox, respects senior's permissions | ✅ guardian screen with one-tap call-back | Push (FCM) is a stub: needs a Firebase project |
| F5 | Scam checker | ✅ WhatsApp webhook (text, links, numbers, contacts, screenshots) + in-app; rules then Claude | ✅ paste/type, or "Share → Kavach" from any app | |
| F6 | Long unknown-call nudge | ✅ | ⚠️ spike: `READ_PHONE_STATE` + our own screened number | Needs Play policy confirmation, see docs/PLAY_POLICY.md |
| F7 | Report & recover | ✅ | ✅ 1930, cybercrime.gov.in, Chakshu, bank block line | Bank block numbers are placeholders |
| F8 | Weekly voice briefing | ❌ | ❌ | P2; not started |
| F9 | Bank risk events + trusted-person approval | ✅ idempotent events, 24h cooling-off before a guardian gains approval power, expiry, bank callback + polling | ✅ approve/decline in guardian screen | See docs/BANK_API.md |
| F10 | Human helper line | ❌ | ❌ | Needs telephony provider + responders |
| F11 | Bank dashboard | ✅ JSON API (`/v1/bank/dashboard`) | n/a | No web UI yet |
| — | DPDP basics | ✅ itemised notice (en/hi/mr), consent records, export, delete | ✅ notice read aloud, delete my data | Legal review required |
| — | MVP metrics | ✅ `/v1/admin/metrics` | | activated pairs, weekly active, alert precision, false alarms, guardian response time |

## Run the backend

```bash
cd backend
pip install -r requirements.txt
python -m pytest -q                 # 25 tests
python scripts/eval_checker.py      # message checker accuracy on data/message_eval.jsonl (rules only)
KAVACH_ENV=dev uvicorn app.main:app --reload --port 8000
# open http://localhost:8000/docs for the interactive API
```

In dev mode the OTP comes back in the API response, and every WhatsApp/push message
is written to the `outbox` table instead of being sent, so you can test the whole flow
without Meta access. Bank API key in dev: `dev-bank-key`. Admin token: `dev-admin`.

To turn on the LLM second opinion set `ANTHROPIC_API_KEY`. The checker then uses
Claude (`claude-opus-5-5`, low effort, JSON-schema output) when the rules aren't
decisive, and for every screenshot. If the API fails or refuses, it falls back to the
rules verdict, so the bot never goes silent. Run `python scripts/eval_checker.py --llm`
to measure it before switching it on (this costs API credit).

## Build the Android app

Open `android/` in Android Studio (Ladybug or newer), let it sync, run on a phone
with Android 10+. In the app, long-press the title on the "Family & privacy" screen
to point it at your dev server (e.g. `http://10.0.2.2:8000` from the emulator; add
a network-security config if you use plain HTTP on a real device).

Test the call warning: add `+919000000001` (a seeded placeholder "scam" number)
to a second phone, or use the emulator's extended controls → Phone → call in.

**Verification status:** the Kotlin sources compile cleanly against the Android 15
framework classes, but the APK itself has not been built or run on a device (the build
machine had no Android SDK). Expect a short round of fixes in Android Studio,
mainly in the manifest and resources.

## Before launch (not code)

- Replace `data/scam_numbers_seed.json` placeholders with verified numbers. A wrong entry tells a senior a genuine caller is a scammer.
- Native-speaker review of every Hindi/Marathi string (`backend/app/services/i18n.py`, `android/.../ui/Strings.kt`).
- Grow `data/message_eval.jsonl` to 200+ real forwarded messages, and keep a held-out set. The current set is 35 messages the rules were tuned on, so the 97% accuracy figure is optimistic.
- WhatsApp: Meta Business verification, an approved utility template `kavach_guardian_alert` with one body parameter.
- SMS OTP provider + DLT registration, Firebase project for push, privacy/terms legal review, grievance officer contact.
- Alembic migrations before the first production deploy (dev uses `create_all`).
