package com.kavach.app.ui

import android.content.ClipboardManager
import android.content.Intent
import android.os.Bundle
import android.text.InputType
import com.kavach.app.data.json

/** F5 in the app: paste or share a message/link/number; get Safe / Suspicious / Scam. */
class CheckMessageActivity : BaseActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (!prefs.loggedIn) { startActivity(Intent(this, MainActivity::class.java)); finish(); return }
        val shared = if (intent?.action == Intent.ACTION_SEND) intent.getStringExtra(Intent.EXTRA_TEXT) else null

        val col = Ui.screen(this)
        col.addView(Ui.title(this, s("check_message")))
        val box = Ui.input(this, s("message_hint"), InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE, lines = 4)
        shared?.let { box.setText(it) }
        col.addView(box)
        col.addView(Ui.button(this, s("paste"), Ui.GREY, 64) {
            val clip = getSystemService(ClipboardManager::class.java)?.primaryClip
            clip?.getItemAt(0)?.coerceToText(this)?.let { box.setText(it) }
        })
        val result = Ui.body(this, "")
        val checkButton = Ui.button(this, s("check"), Ui.BLUE) {
            val text = box.text.toString().trim()
            if (text.isEmpty()) return@button
            result.text = s("checking")
            call("POST", "/v1/check", json("text" to text)) { r ->
                val verdict = r.getString("verdict")
                result.setTextColor(when (verdict) { "scam" -> Ui.RED; "suspicious" -> Ui.AMBER; else -> Ui.GREEN })
                result.text = r.getString("message")
                speaker.say(r.getString("message").lineSequence().take(2).joinToString(" "))
            }
        }
        col.addView(checkButton)
        col.addView(result)
        if (shared != null) col.post { checkButton.performClick() }
    }
}
