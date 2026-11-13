package com.kavach.app.call

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.telephony.TelephonyManager
import com.kavach.app.Config
import com.kavach.app.KavachApp

/**
 * F6 (technical spike). Tracks whether the unknown-number call we screened was answered,
 * and schedules a nudge if it is still going after [Config.LONG_CALL_MS].
 *
 * Needs only READ_PHONE_STATE (call state, no number). The number comes from our own
 * screening step. Confirm with Play policy review before launch - see docs/PLAY_POLICY.md.
 */
class PhoneStateReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != TelephonyManager.ACTION_PHONE_STATE_CHANGED) return
        val prefs = (context.applicationContext as KavachApp).prefs
        val call = prefs.activeCall ?: return
        when (intent.getStringExtra(TelephonyManager.EXTRA_STATE)) {
            TelephonyManager.EXTRA_STATE_OFFHOOK -> {
                val ringingAt = call.optLong("ringing_at")
                // Only an answer shortly after our screened call rang counts as "that call".
                if (call.optLong("answered_at") == 0L && System.currentTimeMillis() - ringingAt < 90_000) {
                    val now = System.currentTimeMillis()
                    prefs.activeCall = call.put("answered_at", now)
                    schedule(context, now + Config.LONG_CALL_MS)
                }
            }
            TelephonyManager.EXTRA_STATE_IDLE -> {
                if (call.optLong("answered_at") != 0L || System.currentTimeMillis() - call.optLong("ringing_at") > 90_000) {
                    prefs.activeCall = null
                    cancel(context)
                }
            }
        }
    }

    companion object {
        private fun pi(ctx: Context) = PendingIntent.getBroadcast(
            ctx, 7, Intent(ctx, LongCallAlarmReceiver::class.java), PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        fun schedule(ctx: Context, atMs: Long) {
            // Inexact is fine for "about 10 minutes" and needs no exact-alarm permission.
            ctx.getSystemService(AlarmManager::class.java)?.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, atMs, pi(ctx))
        }

        fun cancel(ctx: Context) = ctx.getSystemService(AlarmManager::class.java)?.cancel(pi(ctx))
    }
}
