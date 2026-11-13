# Bank partner API (v2): trusted-person approval

Kavach never moves or holds money. The bank pauses a transfer under its own rules
(e.g. RBI's proposed >₹50,000 trusted-person check for customers 70+), and Kavach
carries the decision to and from the customer's trusted family member.

Auth: `X-API-Key: <key>` header, issued per bank (`BANK_API_KEYS`). Production adds mTLS + IP allow-listing.

## Enrolment
The senior links their bank customer reference in the Kavach app (`bank_code`, `bank_customer_ref`).
For a pilot, the bank should verify this link through its own app or branch. That flow is to be agreed with the bank.

## 1. Send a risk event
`POST /v1/bank/risk-events`
```json
{"event_id": "TXN-2026-000123", "customer_ref": "CUST-1", "amount_paise": 7500000,
 "payee_label": "Unknown Traders", "first_time_payee": true,
 "callback_url": "https://bank.example/kavach/callback"}
```
Responses:
- `{"status": "pending", "hold_id": 12, "expires_at": "..."}`: guardians alerted by WhatsApp and in-app.
- `{"status": "no_trusted_person"}`: no guardian has (effective) approval rights; apply your default.
- `404 customer not enrolled`.

Idempotent on `event_id`: resending returns the same hold.

## 2. Learn the decision
Kavach POSTs the hold JSON to `callback_url` on decision or expiry, and you can poll:
`GET /v1/bank/holds/{event_id}` → `status`: `pending | approved | declined | expired`.
`expired` means nobody decided within `HOLD_DECISION_MINUTES` (default 60, matching RBI's proposed 1-hour
cooling-off). The bank decides what expiry means.

## Safeguards against guardian abuse
- Only the senior can grant approval rights, and they take effect **24 hours** after being granted.
- The senior can remove a guardian at any time; approval rights end immediately.
- Every event and decision is in the audit log, visible on `GET /v1/bank/dashboard`.
- Recommended for pilots: require two guardians where possible (not yet enforced).

## 3. Dashboard
`GET /v1/bank/dashboard`: enrolled seniors, holds by status, alerts by kind, declined amount, recent audit log.
