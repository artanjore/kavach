package com.kavach.app.ui

import android.os.Bundle

/** F7 report & recover: one tap each to 1930, the cybercrime portal, Chakshu and the bank. */
class RecoverActivity : BaseActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val col = Ui.screen(this)
        col.addView(Ui.title(this, s("get_help")))
        col.addView(Ui.button(this, "📞 " + s("call_1930"), Ui.RED, 110) { Ui.dial(this, "1930") })
        col.addView(Ui.button(this, s("open_portal"), Ui.BLUE) { Ui.open(this, "https://cybercrime.gov.in") })
        col.addView(Ui.button(this, s("open_chakshu"), Ui.BLUE) { Ui.open(this, "https://sancharsaathi.gov.in/sfc/") })
        call("GET", "/v1/recover", onError = {}) { r ->
            r.getJSONObject("helplines").optJSONObject("bank")?.let { bank ->
                col.addView(Ui.button(this, "📞 ${s("call_bank")} (${bank.optString("name")})", Ui.AMBER) {
                    Ui.dial(this, bank.getString("block_line"))
                })
            }
            val steps = r.getJSONArray("steps")
            for (i in 0 until steps.length()) col.addView(Ui.body(this, "${i + 1}. ${steps.getString(i)}", sizeSp = 20f))
        }
    }
}
