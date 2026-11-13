package com.kavach.app.ui

import android.app.Activity
import com.kavach.app.KavachApp
import com.kavach.app.data.Api
import com.kavach.app.data.ApiError
import org.json.JSONObject

abstract class BaseActivity : Activity() {
    val app get() = application as KavachApp
    val prefs get() = app.prefs
    val api get() = app.api
    val lang get() = prefs.language
    fun s(key: String) = S.get(key, lang)

    private var speakerInstance: Speaker? = null
    val speaker: Speaker
        get() = speakerInstance ?: Speaker(this, lang).also { speakerInstance = it }

    /** Call the API off the main thread; show a friendly error if it fails. */
    fun call(method: String, path: String, body: JSONObject? = null, onError: ((Throwable) -> Unit)? = null, ok: (JSONObject) -> Unit) {
        Api.async({ api.obj(method, path, body) }) { r ->
            if (isFinishing || isDestroyed) return@async
            r.onSuccess(ok).onFailure { e ->
                if (onError != null) onError(e)
                else Ui.toast(this, if (e is ApiError) (e.message ?: s("error")) else s("no_network"))
            }
        }
    }

    override fun onDestroy() {
        speakerInstance?.shutdown()
        super.onDestroy()
    }
}
