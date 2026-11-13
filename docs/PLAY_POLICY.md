# Google Play permissions: what we use and why

| Permission / API | Used for | Restricted? |
|---|---|---|
| `CallScreeningService` + Call Screening role | F2: see the number of incoming calls from non-contacts, before answer | No. Android binds it only after the user grants the role in a system dialog |
| `POST_NOTIFICATIONS` | warnings and alerts | No (runtime prompt) |
| `USE_FULL_SCREEN_INTENT` | show the warning over the lock screen while ringing | On Android 14+ Play auto-grants it only to calling/alarm apps. Declare it in the Play Console; otherwise Android falls back to a heads-up banner, and the spoken warning still plays |
| `READ_PHONE_STATE` | F6 only: know whether the screened call is still off-hook | Dangerous (runtime prompt), not restricted. Optional, asked separately |
| `INTERNET` | API | No |

**Not requested:** `READ_CALL_LOG`, `PROCESS_OUTGOING_CALLS`, `READ_SMS`/`RECEIVE_SMS`, `READ_CONTACTS`, `RECORD_AUDIO`, `CALL_PHONE`, accessibility services.

## F6 spike: open questions
1. Play may ask why a non-dialer app reads phone state. The justification: "detect that a call the user was warned about is still in progress, to offer help". Confirm with a pre-launch review, or drop F6.
2. `ACTION_PHONE_STATE_CHANGED` is on the implicit-broadcast exemption list, so the manifest receiver works without a foreground service. Re-check on each new Android version.
3. Off-hook can't be tied to a specific call without call-log access, so we assume an off-hook within 90 seconds of our screened call ringing is that call. Measure false nudges in the beta.

## Store listing
Never imply government affiliation (no "Cyber Police", no emblems). Say "warns you; you decide".
