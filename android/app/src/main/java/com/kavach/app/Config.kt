package com.kavach.app

object Config {
    /** Production API. Debug builds can override it in Settings -> developer (long-press the title). */
    const val DEFAULT_API_BASE = "https://api.kavach.example"

    /** CallScreeningService must answer the OS within 5 s; keep the network check well under that. */
    const val SCREEN_TIMEOUT_MS = 2500

    /** F6: nudge after an unknown-number call has been off-hook this long. */
    const val LONG_CALL_MS = 10 * 60 * 1000L
}
