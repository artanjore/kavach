# Data handling (engineering view, not legal advice)

| Data | Stored? | Where in code |
|---|---|---|
| Senior/guardian phone, name, language | yes | `users` |
| Caller number, time, level, duration for screened unknown calls | yes; numbers not in contacts only (Android doesn't send us contact calls) | `call_events` |
| Messages/screenshots the user forwards | text yes (≤4,000 chars); images are sent to the LLM and **not stored** | `message_checks` |
| Consent given/withdrawn, with notice version | yes, append-only | `consents` |
| Call audio, SMS inbox, contacts, bank credentials | **never** | n/a |

- Guardians see only what the senior enabled (`pairings.see_*`). Message checks are **off by default**.
- `GET /v1/me/export`: access right. `DELETE /v1/me`: erasure (personal rows deleted, account tombstoned, pairings revoked).
- The LLM provider processes forwarded content: list it as a processor in the privacy notice, and confirm its data-retention and residency terms.
- TODO before launch: 12-month retention job for `call_events`/`message_checks`, encryption at rest (managed Postgres), access logging, breach-response runbook, named grievance officer.
