package com.kavach.app.call

import android.app.Notification
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import com.kavach.app.KavachApp
import com.kavach.app.ui.S
import com.kavach.app.ui.Speaker
import com.kavach.app.ui.WarningActivity

/** Shows the full-screen call warning and speaks it aloud. */
object CallWarnings {
    private const val NOTIF_ID = 1001
    private var lastCallId: Int? = null

    private fun fallbackSpeech(level: String, lang: String): String = when (lang) {
        "hi" -> if (level == "warn") "सावधान। यह कॉल धोखाधड़ी हो सकती है। असली पुलिस या बैंक फ़ोन पर कभी पैसे नहीं माँगते।"
                else "अनजान नंबर। अगर पैसे, OTP माँगें या बात छुपाने को कहें, तो फ़ोन काट दें।"
        "mr" -> if (level == "warn") "सावध. हा कॉल फसवणुकीचा असू शकतो. खरे पोलीस किंवा बँक फोनवर कधीही पैसे मागत नाहीत."
                else "अनोळखी नंबर. पैसे, OTP मागितले किंवा गुप्त ठेवायला सांगितले तर फोन ठेवा."
        else -> if (level == "warn") "Careful. This call may be a scam. Real police and banks never ask for money on a call."
                else "Unknown caller. If they ask for money, an OTP or to keep it secret, hang up."
    }

    fun attachCallId(id: Int) { lastCallId = id }

    fun show(ctx: Context, lang: String, level: String, number: String, speak: String?, callId: Int?) {
        callId?.let { lastCallId = it }
        val text = speak?.takeIf { it.isNotBlank() } ?: fallbackSpeech(level, lang)
        val intent = Intent(ctx, WarningActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP)
            .putExtra("level", level).putExtra("number", number).putExtra("text", text)
            .putExtra("call_id", lastCallId ?: 0)
        val pi = PendingIntent.getActivity(ctx, 0, intent, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)

        val title = S.get(if (level == "warn") "warning_title" else "caution_title", lang)
        val n = Notification.Builder(ctx, KavachApp.CH_CALL_WARNING)
            .setSmallIcon(android.R.drawable.stat_sys_warning)
            .setContentTitle(title)
            .setContentText(text)
            .setStyle(Notification.BigTextStyle().bigText(text))
            .setCategory(Notification.CATEGORY_CALL)
            .setColor(if (level == "warn") 0xFFC62828.toInt() else 0xFFEF6C00.toInt())
            .setContentIntent(pi)
            // Shows over the lock screen while ringing. On Android 14+ this needs the
            // full-screen-intent permission; without it Android shows a heads-up banner instead.
            .setFullScreenIntent(pi, true)
            .setAutoCancel(true)
            .setTimeoutAfter(5 * 60 * 1000L)
            .build()
        ctx.getSystemService(NotificationManager::class.java)?.notify(NOTIF_ID, n)

        // Speak over the ringtone (ringtone is quieter on most phones once TTS plays).
        val sp = Speaker(ctx, lang)
        sp.say(text)
    }
}
