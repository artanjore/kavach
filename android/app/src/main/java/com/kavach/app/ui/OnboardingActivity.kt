package com.kavach.app.ui

import android.Manifest
import android.app.role.RoleManager
import android.content.Intent
import android.os.Bundle
import android.text.InputType
import android.widget.CheckBox
import android.widget.TextView
import com.kavach.app.data.json

/**
 * F1 paired onboarding, designed to be done WITH a family member or volunteer:
 * language -> role -> phone + OTP -> privacy notice read aloud + consent -> permissions -> pairing.
 */
class OnboardingActivity : BaseActivity() {
    private var phone = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        stepLanguage()
    }

    /** Arrived from a scanned QR: whoever scans it is the family member. */
    private val joiningFromQr get() = prefs.pendingJoinCode != null

    private fun stepLanguage() {
        val col = Ui.screen(this)
        col.addView(Ui.title(this, "भाषा / भाषा / Language"))
        listOf("hi" to "हिन्दी", "mr" to "मराठी", "en" to "English").forEach { (code, label) ->
            col.addView(Ui.button(this, label) {
                prefs.language = code
                if (joiningFromQr) { prefs.role = "guardian"; stepPhone() } else stepRole()
            })
        }
    }

    private fun stepRole() {
        val col = Ui.screen(this)
        col.addView(Ui.title(this, s("who_are_you")))
        col.addView(Ui.button(this, s("i_am_senior"), Ui.GREEN, 120) { prefs.role = "senior"; stepPhone() })
        col.addView(Ui.button(this, s("i_am_guardian"), Ui.BLUE, 120) { prefs.role = "guardian"; stepPhone() })
    }

    private fun stepPhone() {
        val col = Ui.screen(this)
        col.addView(Ui.title(this, s("your_phone")))
        val name = Ui.input(this, s("your_name"), InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_WORDS)
        val num = Ui.input(this, "98XXXXXXXX", InputType.TYPE_CLASS_PHONE)
        col.addView(name); col.addView(num)
        col.addView(Ui.button(this, s("send_code"), Ui.GREEN) {
            phone = num.text.toString()
            prefs.name = name.text.toString().trim()
            call("POST", "/v1/auth/otp/request", json("phone" to phone)) { r ->
                stepOtp(r.optString("dev_code", ""))
            }
        })
    }

    private fun stepOtp(devCode: String) {
        val col = Ui.screen(this)
        col.addView(Ui.title(this, s("enter_code")))
        val code = Ui.input(this, "______", InputType.TYPE_CLASS_NUMBER)
        if (devCode.isNotEmpty()) code.setText(devCode) // dev server only
        col.addView(code)
        col.addView(Ui.button(this, s("next"), Ui.GREEN) {
            call("POST", "/v1/auth/otp/verify",
                json("phone" to phone, "code" to code.text.toString(), "role" to prefs.role, "language" to lang, "name" to prefs.name)) { r ->
                prefs.token = r.getString("token")
                stepPrivacy()
            }
        })
    }

    private fun stepPrivacy() {
        call("GET", "/v1/privacy/notice?lang=$lang") { notice ->
            val col = Ui.screen(this)
            col.addView(Ui.title(this, s("privacy_title")))
            val items = notice.getJSONArray("items")
            val spoken = StringBuilder()
            for (i in 0 until items.length()) {
                val it = items.getJSONObject(i)
                col.addView(Ui.body(this, it.getString("title"), Ui.BLUE, 22f))
                col.addView(Ui.body(this, it.getString("text"), sizeSp = 20f))
                spoken.append(it.getString("title")).append(". ").append(it.getString("text")).append(" ")
            }
            speaker.say(spoken.toString())
            col.addView(Ui.button(this, "🔊 " + s("listen_again"), Ui.GREY, 64) { speaker.say(spoken.toString()) })

            val wa = CheckBox(this).apply { text = s("whatsapp_opt_in"); textSize = 22f; isChecked = true }
            col.addView(wa)
            col.addView(Ui.button(this, s("agree"), Ui.GREEN) {
                speaker.stop()
                call("POST", "/v1/consent", json("purpose" to "core_protection", "granted" to true)) {}
                call("POST", "/v1/consent", json("purpose" to "whatsapp_alerts", "granted" to wa.isChecked)) {}
                if (prefs.role == "senior") stepPermissions() else stepJoin()
            })
        }
    }

    // ---------------- senior ----------------
    private fun stepPermissions() {
        val col = Ui.screen(this)
        col.addView(Ui.title(this, s("allow_screening")))
        col.addView(Ui.body(this, s("allow_screening_why")))
        col.addView(Ui.button(this, s("next"), Ui.GREEN) {
            val rm = getSystemService(RoleManager::class.java)!!
            if (rm.isRoleAvailable(RoleManager.ROLE_CALL_SCREENING) && !rm.isRoleHeld(RoleManager.ROLE_CALL_SCREENING)) {
                startActivityForResult(rm.createRequestRoleIntent(RoleManager.ROLE_CALL_SCREENING), REQ_ROLE)
            } else afterRole()
        })
    }

    private fun afterRole() {
        val wanted = mutableListOf(Manifest.permission.POST_NOTIFICATIONS)
        val col = Ui.screen(this)
        col.addView(Ui.title(this, s("allow_long_call")))
        col.addView(Ui.button(this, s("yes"), Ui.GREEN) {
            wanted.add(Manifest.permission.READ_PHONE_STATE); requestPermissions(wanted.toTypedArray(), REQ_PERMS)
        })
        col.addView(Ui.button(this, s("no"), Ui.GREY) { requestPermissions(wanted.toTypedArray(), REQ_PERMS) })
    }

    private fun stepPairCode() {
        call("POST", "/v1/pairing/code") { r ->
            val col = Ui.screen(this)
            col.addView(Ui.title(this, s("add_family")))
            col.addView(Ui.body(this, s("show_code")))
            col.addView(QrView.create(this, r.getString("code")))
            col.addView(TextView(this).apply {
                text = r.getString("code").chunked(3).joinToString(" ")
                textSize = 64f; setTextColor(Ui.INK); textAlignment = TextView.TEXT_ALIGNMENT_CENTER
            })
            col.addView(Ui.button(this, s("done"), Ui.GREEN) { finishOnboarding() })
        }
    }

    // ---------------- guardian ----------------
    private fun stepJoin() {
        val col = Ui.screen(this)
        col.addView(Ui.title(this, s("join_code")))
        val code = Ui.input(this, "123 456", InputType.TYPE_CLASS_NUMBER)
        prefs.pendingJoinCode?.let { code.setText(it); prefs.pendingJoinCode = null }
        col.addView(code)
        col.addView(Ui.button(this, s("next"), Ui.GREEN) {
            call("POST", "/v1/pairing/join", json("code" to code.text.toString().filter { it.isDigit() })) { finishOnboarding() }
        })
    }

    private fun finishOnboarding() {
        startActivity(Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK or Intent.FLAG_ACTIVITY_NEW_TASK))
        finish()
    }

    @Deprecated("Activity result API without androidx")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQ_ROLE) afterRole()
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQ_PERMS) stepPairCode()
    }

    companion object {
        private const val REQ_ROLE = 1
        private const val REQ_PERMS = 2
    }
}
