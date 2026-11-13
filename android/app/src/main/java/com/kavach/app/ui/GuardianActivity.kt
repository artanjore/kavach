package com.kavach.app.ui

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.LinearLayout
import com.kavach.app.data.Api
import com.kavach.app.data.json
import org.json.JSONArray

/**
 * Guardian home (F4 + F9): alert inbox with one-tap call-back, and pending bank transfer holds
 * to approve or decline. Primary alert channel is WhatsApp; this screen refreshes every 30 s while open.
 */
class GuardianActivity : BaseActivity() {
    private val handler = Handler(Looper.getMainLooper())
    private val refresh = object : Runnable {
        override fun run() { load(); handler.postDelayed(this, 30_000) }
    }

    override fun onResume() { super.onResume(); handler.post(refresh) }
    override fun onPause() { handler.removeCallbacks(refresh); super.onPause() }

    private fun load() {
        Api.async({ Pair(api.arr("/v1/holds"), api.arr("/v1/alerts")) }) { r ->
            if (isFinishing) return@async
            val col = Ui.screen(this)
            r.onSuccess { (holds, alerts) ->
                renderHolds(col, holds)
                col.addView(Ui.title(this, s("alerts")))
                if (alerts.length() == 0) col.addView(Ui.body(this, s("no_alerts"), Ui.GREY))
                for (i in 0 until alerts.length()) {
                    val a = alerts.getJSONObject(i)
                    val senior = a.getJSONObject("senior")
                    col.addView(Ui.body(this, a.getString("created_at").take(16).replace('T', ' '), Ui.GREY, 16f))
                    col.addView(Ui.body(this, a.getString("detail"), if (a.getBoolean("acknowledged")) Ui.GREY else Ui.INK, 20f))
                    col.addView(Ui.button(this, "📞 ${s("call")} ${senior.optString("name")}", Ui.GREEN, 72) {
                        call("POST", "/v1/alerts/${a.getInt("id")}/ack", json("called_back" to true)) {}
                        Ui.dial(this, senior.getString("phone"))
                    })
                }
            }.onFailure { col.addView(Ui.body(this, s("no_network"))) }
        }
    }

    private fun renderHolds(col: LinearLayout, holds: JSONArray) {
        val pending = (0 until holds.length()).map { holds.getJSONObject(it) }.filter { it.getString("status") == "pending" }
        if (pending.isEmpty()) return
        col.addView(Ui.title(this, s("pending_transfers"), Ui.RED))
        for (h in pending) {
            val rupees = "%,d".format(h.getLong("amount_paise") / 100)
            col.addView(Ui.body(this, "${h.optString("senior")}: ₹$rupees → ${h.optString("payee_label")}\n(${h.optString("bank")})", Ui.INK, 22f))
            col.addView(Ui.button(this, s("decline"), Ui.RED) { decide(h.getInt("hold_id"), "decline") })
            col.addView(Ui.button(this, s("approve"), Ui.GREY, 64) {
                Ui.confirm(this, lang, s("sure")) { decide(h.getInt("hold_id"), "approve") }
            })
        }
    }

    private fun decide(id: Int, decision: String) =
        call("POST", "/v1/holds/$id/decision", json("decision" to decision)) { load() }
}
