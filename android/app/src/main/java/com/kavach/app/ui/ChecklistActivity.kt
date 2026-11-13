package com.kavach.app.ui

import android.os.Bundle
import com.kavach.app.data.json
import org.json.JSONArray
import org.json.JSONObject

/**
 * F3 "Am I being scammed?" - a 30-second spoken checklist. Pressing the button already
 * alerts the guardian (if the senior allowed it). Any "yes" -> stop-and-call screen.
 * Framed as a normal check, never as blame.
 */
class ChecklistActivity : BaseActivity() {
    private val answers = JSONObject()
    private var questions = JSONArray()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val col = Ui.screen(this)
        col.addView(Ui.title(this, s("checking")))
        call("POST", "/v1/help/pressed", onError = { offline() }) { r ->
            questions = r.getJSONArray("questions")
            ask(0)
        }
    }

    private fun ask(i: Int) {
        if (i >= questions.length()) { submit(); return }
        val q = questions.getJSONObject(i)
        val col = Ui.screen(this)
        col.addView(Ui.body(this, "${i + 1} / ${questions.length()}", Ui.GREY, 18f))
        col.addView(Ui.title(this, q.getString("text")))
        speaker.say(q.getString("text"))
        col.addView(Ui.button(this, s("yes"), Ui.RED, 120) { answers.put(q.getString("id"), true); ask(i + 1) })
        col.addView(Ui.button(this, s("no"), Ui.GREEN, 120) { answers.put(q.getString("id"), false); ask(i + 1) })
        col.addView(Ui.button(this, "🔊", Ui.GREY, 64) { speaker.say(q.getString("text")) })
    }

    private fun submit() {
        call("POST", "/v1/help/checklist", json("answers" to answers), onError = { offline() }) { r ->
            if (r.getBoolean("risk")) stopScreen(r) else okScreen(r.getString("speak"))
        }
    }

    private fun stopScreen(r: JSONObject) {
        val col = Ui.screen(this, Ui.RED)
        val text = r.getString("speak")
        col.addView(Ui.title(this, "🛑", 0xFFFFFFFF.toInt()))
        col.addView(Ui.title(this, text, 0xFFFFFFFF.toInt()))
        speaker.say(text)
        val guardians = r.optJSONArray("call_guardians") ?: JSONArray()
        for (i in 0 until guardians.length()) {
            val g = guardians.getJSONObject(i)
            col.addView(Ui.button(this, "📞 ${s("call")} ${g.optString("name").ifBlank { g.getString("phone") }}", Ui.GREEN, 110) {
                Ui.dial(this, g.getString("phone"))
            })
        }
        col.addView(Ui.button(this, "📞 " + s("call_1930"), Ui.INK) { Ui.dial(this, "1930") })
    }

    private fun okScreen(text: String) {
        val col = Ui.screen(this)
        col.addView(Ui.title(this, "✅"))
        col.addView(Ui.title(this, text))
        speaker.say(text)
        col.addView(Ui.button(this, s("done"), Ui.GREEN) { finish() })
    }

    /** No network: still give the safe advice and the numbers to call. */
    private fun offline() {
        val col = Ui.screen(this, Ui.RED)
        col.addView(Ui.title(this, s("no_network"), 0xFFFFFFFF.toInt()))
        speaker.say(s("no_network"))
        val g = prefs.guardians
        for (i in 0 until g.length()) {
            val o = g.getJSONObject(i)
            col.addView(Ui.button(this, "📞 ${s("call")} ${o.optString("name")}", Ui.GREEN, 110) { Ui.dial(this, o.getString("phone")) })
        }
        col.addView(Ui.button(this, "📞 " + s("call_1930"), Ui.INK) { Ui.dial(this, "1930") })
    }
}
