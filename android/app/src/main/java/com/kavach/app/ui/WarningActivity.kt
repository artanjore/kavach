package com.kavach.app.ui

import android.content.Intent
import android.os.Bundle
import com.kavach.app.data.json

/** Full-screen F2 warning while a suspicious call rings. */
class WarningActivity : BaseActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        render(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        render(intent)
    }

    private fun render(i: Intent) {
        val level = i.getStringExtra("level") ?: "caution"
        val number = i.getStringExtra("number").orEmpty()
        val text = i.getStringExtra("text").orEmpty()
        val callId = i.getIntExtra("call_id", 0)
        val white = 0xFFFFFFFF.toInt()

        val col = Ui.screen(this, if (level == "warn") Ui.RED else Ui.AMBER)
        col.addView(Ui.title(this, "⚠️ " + s(if (level == "warn") "warning_title" else "caution_title"), white))
        col.addView(Ui.body(this, number, white, 28f))
        col.addView(Ui.body(this, text, white, 24f))
        col.addView(Ui.button(this, s("careful"), Ui.INK) { finish() })
        col.addView(Ui.button(this, "🔊 " + s("listen_again"), Ui.GREY, 64) { speaker.say(text) })
        if (callId > 0) {
            col.addView(Ui.button(this, s("was_genuine"), Ui.GREY, 64) {
                call("POST", "/v1/calls/$callId/outcome", json("outcome" to "genuine")) { finish() }
            })
        }
        col.addView(Ui.button(this, s("call_family"), Ui.GREEN) {
            startActivity(Intent(this, MainActivity::class.java)); finish()
        })
    }
}
