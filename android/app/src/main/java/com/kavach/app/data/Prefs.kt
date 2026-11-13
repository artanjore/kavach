package com.kavach.app.data

import android.content.Context
import com.kavach.app.Config
import org.json.JSONArray
import org.json.JSONObject

/** Small local store. Holds no call history: only the call currently in progress. */
class Prefs(context: Context) {
    private val sp = context.getSharedPreferences("kavach", Context.MODE_PRIVATE)

    var apiBase: String
        get() = sp.getString("api_base", Config.DEFAULT_API_BASE)!!
        set(v) = sp.edit().putString("api_base", v.trimEnd('/')).apply()

    var token: String?
        get() = sp.getString("token", null)
        set(v) = sp.edit().putString("token", v).apply()

    var role: String
        get() = sp.getString("role", "senior")!!
        set(v) = sp.edit().putString("role", v).apply()

    var language: String
        get() = sp.getString("language", "hi")!!
        set(v) = sp.edit().putString("language", v).apply()

    var name: String
        get() = sp.getString("name", "")!!
        set(v) = sp.edit().putString("name", v).apply()

    /** Guardians to call from the stop screen: [{"name":..,"phone":..}] */
    var guardians: JSONArray
        get() = JSONArray(sp.getString("guardians", "[]"))
        set(v) = sp.edit().putString("guardians", v.toString()).apply()

    /** Offline copy of the scam-number list, refreshed when the app opens. */
    var scamNumbers: Set<String>
        get() = sp.getStringSet("scam_numbers", emptySet())!!
        set(v) = sp.edit().putStringSet("scam_numbers", v).apply()

    /** The unknown-number call being tracked for F6, or null. */
    var activeCall: JSONObject?
        get() = sp.getString("active_call", null)?.let { JSONObject(it) }
        set(v) = sp.edit().putString("active_call", v?.toString()).apply()

    val loggedIn get() = token != null

    fun clear() = sp.edit().clear().apply()
}
