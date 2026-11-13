package com.kavach.app.call

import android.app.Notification
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.telephony.TelephonyManager
import com.kavach.app.KavachApp
import com.kavach.app.data.Api
import com.kavach.app.data.json
import com.kavach.app.ui.ChecklistActivity
import com.kavach.app.ui.S
import com.kavach.app.ui.Speaker

/** Fires ~10 min into an answered unknown-number call: gentle nudge + guardian alert. */
class LongCallAlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val app = context.applicationContext as KavachApp
        val prefs = app.prefs
        val call = prefs.activeCall ?: return
        val answeredAt = call.optLong("answered_at")
        if (answeredAt == 0L) return

        val tm = context.getSystemService(TelephonyManager::class.java)
        @Suppress("DEPRECATION")
        val stillOnCall = runCatching { tm!!.callState == TelephonyManager.CALL_STATE_OFFHOOK }.getOrDefault(true)
        if (!stillOnCall) { prefs.activeCall = null; return }

        val durationS = ((System.currentTimeMillis() - answeredAt) / 1000).toInt()
        val pending = goAsync()
        Api.async({
            app.api.obj("POST", "/v1/calls/long-call",
                json("call_id" to call.optInt("call_id").takeIf { it > 0 }, "number" to call.optString("number"), "duration_s" to durationS))
        }) { r ->
            val lang = prefs.language
            val text = r.getOrNull()?.optString("speak")?.takeIf { it.isNotBlank() } ?: S.get("long_call_title", lang)
            val open = PendingIntent.getActivity(context, 8,
                Intent(context, ChecklistActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK), PendingIntent.FLAG_IMMUTABLE)
            val n = Notification.Builder(context, KavachApp.CH_CALL_WARNING)
                .setSmallIcon(android.R.drawable.stat_sys_warning)
                .setContentTitle(S.get("long_call_title", lang))
                .setContentText(text)
                .setStyle(Notification.BigTextStyle().bigText(text))
                .setContentIntent(open).setAutoCancel(true).build()
            context.getSystemService(NotificationManager::class.java)?.notify(1002, n)
            Speaker(context, lang).say(text)
            // Remind once more after another 10 minutes if the call continues.
            if (durationS < 25 * 60) PhoneStateReceiver.schedule(context, System.currentTimeMillis() + 10 * 60 * 1000L)
            pending.finish()
        }
    }
}
