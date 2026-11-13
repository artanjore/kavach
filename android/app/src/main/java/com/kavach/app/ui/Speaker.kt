package com.kavach.app.ui

import android.content.Context
import android.speech.tts.TextToSpeech
import java.util.Locale

/** Text-to-speech in the senior's language. Speaks queued text once the engine is ready. */
class Speaker(context: Context, private val lang: String) {
    private var ready = false
    private val pending = mutableListOf<String>()
    private val tts: TextToSpeech = TextToSpeech(context.applicationContext) { status ->
        if (status == TextToSpeech.SUCCESS) {
            val locale = Locale.forLanguageTag(
                when (lang) { "hi" -> "hi-IN"; "mr" -> "mr-IN"; else -> "en-IN" }
            )
            val r = tts.setLanguage(locale)
            if (r == TextToSpeech.LANG_MISSING_DATA || r == TextToSpeech.LANG_NOT_SUPPORTED) {
                tts.setLanguage(Locale.forLanguageTag("hi-IN")) // Google TTS ships Hindi on most Indian phones
            }
            tts.setSpeechRate(0.85f) // a little slower for older listeners
            ready = true
            pending.forEach { say(it, TextToSpeech.QUEUE_ADD) }
            pending.clear()
        }
    }

    fun say(text: String, mode: Int = TextToSpeech.QUEUE_FLUSH) {
        if (text.isBlank()) return
        if (!ready) { pending.add(text); return }
        tts.speak(text, mode, null, text.hashCode().toString())
    }

    fun stop() = tts.stop()
    fun shutdown() = tts.shutdown()
}
