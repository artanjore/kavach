package com.kavach.app.data

/** Mirror of backend app/risk/phone.py normalize(), for the offline scam-list lookup. */
object PhoneNumbers {
    fun normalize(raw: String?): String {
        val s = raw?.trim().orEmpty()
        val digits = s.filter { it.isDigit() }
        if (digits.isEmpty()) return ""
        if (s.startsWith("+")) return "+$digits"
        if (digits.startsWith("00")) return "+" + digits.drop(2)
        if (digits.length == 10 && digits[0] in "6789") return "+91$digits"
        if (digits.length == 11 && digits[0] == '0' && digits[1] in "6789") return "+91" + digits.drop(1)
        if (digits.length == 12 && digits.startsWith("91") && digits[2] in "6789") return "+$digits"
        return digits
    }
}
