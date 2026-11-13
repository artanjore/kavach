package com.kavach.app.ui

import android.content.Intent
import android.os.Bundle
import com.kavach.app.data.Api
import com.kavach.app.data.json
import org.json.JSONArray

/** Senior home screen. Routes to onboarding or the guardian screen when needed. */
class MainActivity : BaseActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        route(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        route(intent)
    }

    private fun route(i: Intent?) {
        // kavach://join?code=123456 from the pairing QR
        i?.data?.takeIf { it.scheme == "kavach" && it.host == "join" }?.getQueryParameter("code")
            ?.filter { it.isDigit() }?.takeIf { it.length == 6 }?.let { prefs.pendingJoinCode = it }

        if (!prefs.loggedIn) { startActivity(Intent(this, OnboardingActivity::class.java)); finish(); return }
        if (prefs.role == "guardian") {
            val code = prefs.pendingJoinCode
            if (code != null) {
                prefs.pendingJoinCode = null
                call("POST", "/v1/pairing/join", json("code" to code)) { goGuardian() }
            } else goGuardian()
        }
    }

    private fun goGuardian() { startActivity(Intent(this, GuardianActivity::class.java)); finish() }

    override fun onResume() {
        super.onResume()
        if (!prefs.loggedIn || prefs.role != "senior") return
        render()
        refreshCaches()
    }

    private fun render() {
        val col = Ui.screen(this)
        col.addView(Ui.title(this, if (prefs.name.isNotBlank()) "🙏 ${prefs.name}" else "Kavach"))
        col.addView(Ui.button(this, s("help_button"), Ui.RED, heightDp = 220) {
            startActivity(Intent(this, ChecklistActivity::class.java))
        })
        col.addView(Ui.button(this, s("call_family"), Ui.GREEN) { callFamily() })
        col.addView(Ui.button(this, s("check_message"), Ui.BLUE) {
            startActivity(Intent(this, CheckMessageActivity::class.java))
        })
        col.addView(Ui.button(this, s("get_help"), Ui.AMBER) { startActivity(Intent(this, RecoverActivity::class.java)) })
        col.addView(Ui.button(this, s("settings"), Ui.GREY, heightDp = 64) { startActivity(Intent(this, SettingsActivity::class.java)) })
        col.addView(Ui.body(this, s("disclaimer"), Ui.GREY, 16f))
    }

    private fun callFamily() {
        val g = prefs.guardians
        if (g.length() == 0) { startActivity(Intent(this, SettingsActivity::class.java)); return }
        Ui.dial(this, g.getJSONObject(0).getString("phone"))
    }

    /** Keep the offline scam list and the guardian list fresh for when the network is bad. */
    private fun refreshCaches() {
        Api.async({ api.obj("GET", "/v1/scam-numbers") }) { r ->
            r.onSuccess { o ->
                val arr = o.getJSONArray("numbers")
                prefs.scamNumbers = (0 until arr.length()).map { arr.getString(it) }.toSet()
            }
        }
        Api.async({ api.arr("/v1/pairing") }) { r ->
            r.onSuccess { arr ->
                val out = JSONArray()
                for (i in 0 until arr.length()) out.put(arr.getJSONObject(i).getJSONObject("guardian"))
                prefs.guardians = out
            }
        }
    }
}
