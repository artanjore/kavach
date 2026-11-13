package com.kavach.app.call

import android.telecom.Call
import android.telecom.CallScreeningService
import com.kavach.app.Config
import com.kavach.app.KavachApp
import com.kavach.app.data.Api
import com.kavach.app.data.PhoneNumbers
import com.kavach.app.data.json
import org.json.JSONObject

/**
 * F2 pre-answer warning.
 *
 * Android calls this for incoming calls from numbers that are NOT in the user's contacts,
 * once the user has granted Kavach the Call Screening role. We always let the call ring
 * (we warn, the senior decides) and show/speak a warning in parallel.
 *
 * Uses no call-log, contacts or SMS permission.
 */
class ScamScreeningService : CallScreeningService() {

    override fun onScreenCall(details: Call.Details) {
        // Answer the OS immediately: never block, silence or reject. The warning is separate.
        respondToCall(details, CallResponse.Builder().build())
        if (details.callDirection != Call.Details.DIRECTION_INCOMING) return

        val app = application as KavachApp
        val prefs = app.prefs
        if (!prefs.loggedIn || prefs.role != "senior") return

        val raw = details.handle?.schemeSpecificPart.orEmpty()
        val number = PhoneNumbers.normalize(raw)
        val startedRinging = System.currentTimeMillis()
        prefs.activeCall = json("number" to number, "ringing_at" to startedRinging, "answered_at" to 0L, "call_id" to 0)

        // 1) Instant offline answer from the cached scam list.
        if (number in prefs.scamNumbers) {
            CallWarnings.show(this, prefs.language, "warn", number, null, null)
        }

        // 2) Server check (scam list + reports + repeat-call + shape). Short timeout.
        Api.async({
            app.api.obj("POST", "/v1/calls/screen", json("number" to raw), timeoutMs = Config.SCREEN_TIMEOUT_MS)
        }) { result ->
            result.onSuccess { r: JSONObject ->
                val level = r.optString("level", "safe")
                prefs.activeCall = prefs.activeCall?.put("call_id", r.optInt("call_id"))
                if (level != "safe" && number !in prefs.scamNumbers) {
                    CallWarnings.show(this, prefs.language, level, number, r.optString("speak"), r.optInt("call_id"))
                } else if (level != "safe") {
                    CallWarnings.attachCallId(r.optInt("call_id"))
                }
            }
            // On failure the cached result (if any) already showed; otherwise stay quiet rather than
            // warn on every unknown call - false alarms erode trust fastest.
        }
    }
}
