package com.kavach.app.data

import android.os.Handler
import android.os.Looper
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

class ApiError(val code: Int, message: String) : IOException(message)

/** Minimal JSON-over-HTTPS client on HttpURLConnection (no third-party libraries). */
class Api(private val prefs: Prefs) {

    fun request(method: String, path: String, body: JSONObject? = null, timeoutMs: Int = 10_000): String {
        val conn = URL(prefs.apiBase + path).openConnection() as HttpURLConnection
        try {
            conn.requestMethod = method
            conn.connectTimeout = timeoutMs
            conn.readTimeout = timeoutMs
            conn.setRequestProperty("Accept", "application/json")
            prefs.token?.let { conn.setRequestProperty("Authorization", "Bearer $it") }
            if (body != null) {
                conn.doOutput = true
                conn.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                conn.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            }
            val code = conn.responseCode
            val stream = if (code in 200..299) conn.inputStream else conn.errorStream
            val text = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
            if (code !in 200..299) {
                val detail = runCatching { JSONObject(text).optString("detail") }.getOrNull()
                throw ApiError(code, detail?.ifBlank { null } ?: "HTTP $code")
            }
            return text
        } finally {
            conn.disconnect()
        }
    }

    fun obj(method: String, path: String, body: JSONObject? = null, timeoutMs: Int = 10_000) =
        JSONObject(request(method, path, body, timeoutMs))

    fun arr(path: String) = JSONArray(request("GET", path))

    companion object {
        private val pool = Executors.newFixedThreadPool(3)
        private val main = Handler(Looper.getMainLooper())

        /** Run [work] off the main thread, deliver the result on the main thread. */
        fun <T> async(work: () -> T, done: (Result<T>) -> Unit) {
            pool.execute {
                val r = runCatching(work)
                main.post { done(r) }
            }
        }
    }
}

fun json(vararg pairs: Pair<String, Any?>): JSONObject = JSONObject().apply { pairs.forEach { (k, v) -> put(k, v) } }
