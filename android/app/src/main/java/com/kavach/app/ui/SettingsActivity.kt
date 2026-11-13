package com.kavach.app.ui

import android.content.Intent
import android.os.Bundle
import android.widget.Switch
import com.kavach.app.data.Api
import com.kavach.app.data.json
import org.json.JSONObject

/** Senior controls: what each family member sees, removing them, deleting data. Dignity over surveillance. */
class SettingsActivity : BaseActivity() {
    override fun onResume() {
        super.onResume()
        Api.async({ api.arr("/v1/pairing") }) { r ->
            if (isFinishing) return@async
            val col = Ui.screen(this)
            col.addView(Ui.title(this, s("settings")))
            r.onSuccess { arr ->
                for (i in 0 until arr.length()) guardianCard(col, arr.getJSONObject(i))
            }.onFailure { col.addView(Ui.body(this, s("no_network"))) }
            col.addView(Ui.button(this, s("add_family"), Ui.GREEN) { showCode() })
            col.addView(Ui.spacer(this, 24))
            col.addView(Ui.button(this, s("delete_data"), Ui.GREY, 64) {
                Ui.confirm(this, lang, s("sure")) {
                    call("DELETE", "/v1/me") {
                        prefs.clear()
                        startActivity(Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK or Intent.FLAG_ACTIVITY_NEW_TASK))
                    }
                }
            })
            // Long-press the title to point a test build at a dev server.
            col.getChildAt(0).setOnLongClickListener { devServerDialog(); true }
        }
    }

    private fun guardianCard(col: android.widget.LinearLayout, p: JSONObject) {
        val g = p.getJSONObject("guardian")
        val perms = p.getJSONObject("permissions")
        col.addView(Ui.body(this, "👤 ${g.optString("name").ifBlank { g.getString("phone") }}", Ui.BLUE, 26f))
        listOf("see_call_warnings" to "can_see_calls", "see_help_presses" to "can_see_help",
               "see_message_checks" to "can_see_checks", "approve_transfers" to "can_approve").forEach { (key, label) ->
            col.addView(Switch(this).apply {
                text = s(label); textSize = 20f; isChecked = perms.getBoolean(key)
                setPadding(0, Ui.dp(context, 10), 0, Ui.dp(context, 10))
                setOnCheckedChangeListener { _, on -> call("PATCH", "/v1/pairing/${p.getInt("id")}", json(key to on)) {} }
            })
        }
        col.addView(Ui.button(this, s("remove"), Ui.GREY, 64) {
            Ui.confirm(this, lang, s("sure")) { call("DELETE", "/v1/pairing/${p.getInt("id")}") { recreate() } }
        })
        col.addView(Ui.spacer(this))
    }

    private fun showCode() = call("POST", "/v1/pairing/code") { r ->
        android.app.AlertDialog.Builder(this).setTitle(s("show_code"))
            .setMessage(r.getString("code").chunked(3).joinToString(" "))
            .setPositiveButton(s("done"), null).show()
    }

    private fun devServerDialog() {
        val input = Ui.input(this, prefs.apiBase).apply { setText(prefs.apiBase) }
        android.app.AlertDialog.Builder(this).setTitle("API server").setView(input)
            .setPositiveButton("OK") { _, _ -> prefs.apiBase = input.text.toString() }.show()
    }
}
