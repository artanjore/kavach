package com.kavach.app

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import com.kavach.app.data.Api
import com.kavach.app.data.Prefs

class KavachApp : Application() {
    lateinit var prefs: Prefs
        private set
    lateinit var api: Api
        private set

    override fun onCreate() {
        super.onCreate()
        instance = this
        prefs = Prefs(this)
        api = Api(prefs)
        val nm = getSystemService(NotificationManager::class.java)!!
        nm.createNotificationChannel(
            NotificationChannel(CH_CALL_WARNING, "Scam call warnings", NotificationManager.IMPORTANCE_HIGH)
                .apply { description = "Warns you while a suspicious call is ringing" }
        )
        nm.createNotificationChannel(
            NotificationChannel(CH_GUARDIAN, "Family alerts", NotificationManager.IMPORTANCE_HIGH)
                .apply { description = "Alerts when your family member may be targeted" }
        )
    }

    companion object {
        const val CH_CALL_WARNING = "call_warning"
        const val CH_GUARDIAN = "guardian"
        lateinit var instance: KavachApp
            private set
    }
}
