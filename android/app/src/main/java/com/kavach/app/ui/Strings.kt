package com.kavach.app.ui

/**
 * On-screen text. Spoken text comes from the server (already localised), so it stays in
 * step with the risk engine. Have a native writer review all of these before launch.
 */
object S {
    private val t: Map<String, Map<String, String>> = mapOf(
        "help_button" to m("Am I being\nscammed?", "क्या मेरे साथ\nधोखा हो रहा है?", "माझी फसवणूक\nहोत आहे का?"),
        "check_message" to m("Check a message", "मैसेज जाँचें", "मेसेज तपासा"),
        "call_family" to m("Call my family", "परिवार को कॉल करें", "कुटुंबाला कॉल करा"),
        "get_help" to m("Report & get help", "शिकायत और मदद", "तक्रार आणि मदत"),
        "settings" to m("Family & privacy", "परिवार और गोपनीयता", "कुटुंब आणि गोपनीयता"),
        "yes" to m("Yes", "हाँ", "हो"),
        "no" to m("No", "नहीं", "नाही"),
        "call" to m("Call", "कॉल करें", "कॉल करा"),
        "call_1930" to m("Call 1930 (Cyber fraud helpline)", "1930 पर कॉल करें (साइबर हेल्पलाइन)", "1930 वर कॉल करा (सायबर हेल्पलाइन)"),
        "open_portal" to m("Report on cybercrime.gov.in", "cybercrime.gov.in पर शिकायत", "cybercrime.gov.in वर तक्रार"),
        "open_chakshu" to m("Report the number (Chakshu)", "नंबर की शिकायत (चक्षु)", "नंबरची तक्रार (चक्षु)"),
        "call_bank" to m("Call my bank to block", "बैंक को कॉल करके ब्लॉक करें", "बँकेला कॉल करून ब्लॉक करा"),
        "warning_title" to m("Possible scam call", "संभावित धोखाधड़ी कॉल", "संभाव्य फसवणूक कॉल"),
        "caution_title" to m("Unknown caller - be careful", "अनजान कॉलर - सावधान रहें", "अनोळखी कॉलर - सावध रहा"),
        "careful" to m("OK, I will be careful", "ठीक है, मैं सावधान रहूँगा", "ठीक आहे, मी सावध राहीन"),
        "was_genuine" to m("This call was genuine", "यह कॉल असली थी", "हा कॉल खरा होता"),
        "paste" to m("Paste", "पेस्ट करें", "पेस्ट करा"),
        "check" to m("Check", "जाँचें", "तपासा"),
        "message_hint" to m("Paste or type the message, link or number", "मैसेज, लिंक या नंबर यहाँ डालें", "मेसेज, लिंक किंवा नंबर इथे टाका"),
        "checking" to m("Checking…", "जाँच हो रही है…", "तपासत आहे…"),
        "no_network" to m("No internet. If anyone asks for money, OTP or PIN - do not share. Call your family.", "इंटरनेट नहीं है। कोई पैसे, OTP या PIN माँगे तो न दें। परिवार को कॉल करें।", "इंटरनेट नाही. कोणी पैसे, OTP किंवा PIN मागितला तर देऊ नका. कुटुंबाला कॉल करा."),
        "choose_language" to m("Choose your language", "अपनी भाषा चुनें", "तुमची भाषा निवडा"),
        "who_are_you" to m("Who will use this phone?", "यह फ़ोन कौन इस्तेमाल करेगा?", "हा फोन कोण वापरणार?"),
        "i_am_senior" to m("Me - protect me", "मैं - मेरी सुरक्षा करें", "मी - माझे संरक्षण करा"),
        "i_am_guardian" to m("I am a family member", "मैं परिवार का सदस्य हूँ", "मी कुटुंबातील सदस्य आहे"),
        "your_name" to m("Your name", "आपका नाम", "तुमचे नाव"),
        "your_phone" to m("Your mobile number", "आपका मोबाइल नंबर", "तुमचा मोबाईल नंबर"),
        "send_code" to m("Send code", "कोड भेजें", "कोड पाठवा"),
        "enter_code" to m("Enter the 6-digit code", "6 अंकों का कोड डालें", "6 अंकी कोड टाका"),
        "next" to m("Next", "आगे", "पुढे"),
        "agree" to m("I agree", "मैं सहमत हूँ", "मी सहमत आहे"),
        "privacy_title" to m("Your privacy", "आपकी गोपनीयता", "तुमची गोपनीयता"),
        "listen_again" to m("Listen again", "फिर से सुनें", "पुन्हा ऐका"),
        "allow_screening" to m("Allow Kavach to check incoming calls", "कवच को आने वाली कॉल जाँचने दें", "कवचला येणारे कॉल तपासू द्या"),
        "allow_screening_why" to m("Kavach only looks at the number of callers who are not in your contacts. It never records or listens to calls.", "कवच सिर्फ़ उन नंबरों को देखता है जो आपके कॉन्टैक्ट में नहीं हैं। यह कॉल न रिकॉर्ड करता है, न सुनता है।", "कवच फक्त तुमच्या संपर्कात नसलेले नंबर पाहते. ते कॉल रेकॉर्ड करत नाही, ऐकत नाही."),
        "allow_long_call" to m("Also warn me on very long calls from unknown numbers (optional)", "अनजान नंबर की बहुत लंबी कॉल पर भी चेतावनी दें (वैकल्पिक)", "अनोळखी नंबरच्या खूप लांब कॉलवरही इशारा द्या (पर्यायी)"),
        "add_family" to m("Add a family member", "परिवार के सदस्य को जोड़ें", "कुटुंबातील सदस्य जोडा"),
        "show_code" to m("Ask your family member to open Kavach and enter this code:", "परिवार के सदस्य से कवच खोलकर यह कोड डालने को कहें:", "कुटुंबातील सदस्याला कवच उघडून हा कोड टाकायला सांगा:"),
        "done" to m("Done", "हो गया", "झाले"),
        "join_code" to m("Enter the code shown on your parent's phone", "माता-पिता के फ़ोन पर दिखा कोड डालें", "आई-वडिलांच्या फोनवरील कोड टाका"),
        "whatsapp_opt_in" to m("Send me alerts on WhatsApp", "मुझे WhatsApp पर अलर्ट भेजें", "मला WhatsApp वर अलर्ट पाठवा"),
        "alerts" to m("Alerts", "अलर्ट", "अलर्ट"),
        "no_alerts" to m("No alerts. All quiet.", "कोई अलर्ट नहीं।", "कोणतेही अलर्ट नाहीत."),
        "approve" to m("Approve", "मंज़ूर", "मंजूर"),
        "decline" to m("Decline", "अस्वीकार", "नामंजूर"),
        "pending_transfers" to m("Transfers waiting for you", "आपकी मंज़ूरी के लिए ट्रांसफ़र", "तुमच्या मंजुरीसाठी ट्रान्सफर"),
        "can_see_calls" to m("Can see scam-call warnings", "धोखाधड़ी कॉल की चेतावनी देख सकते हैं", "फसवणूक कॉलचे इशारे पाहू शकतात"),
        "can_see_help" to m("Is told when I press Help", "मदद बटन दबाने पर सूचना मिलती है", "मदत बटण दाबल्यावर कळवले जाते"),
        "can_see_checks" to m("Is told when I check a scam message", "धोखाधड़ी मैसेज जाँचने पर सूचना मिलती है", "फसवणुकीचा मेसेज तपासल्यावर कळवले जाते"),
        "can_approve" to m("Can approve my large bank transfers (starts after 24 hours)", "मेरे बड़े बैंक ट्रांसफ़र मंज़ूर कर सकते हैं (24 घंटे बाद से)", "माझे मोठे बँक ट्रान्सफर मंजूर करू शकतात (24 तासांनंतर)"),
        "remove" to m("Remove this person", "इन्हें हटाएँ", "यांना काढा"),
        "delete_data" to m("Delete all my data", "मेरा सारा डेटा मिटाएँ", "माझा सर्व डेटा हटवा"),
        "sure" to m("Are you sure?", "क्या आप पक्का हैं?", "नक्की?"),
        "error" to m("Something went wrong. Please try again.", "कुछ गड़बड़ हुई। फिर से कोशिश करें।", "काहीतरी चुकले. पुन्हा प्रयत्न करा."),
        "long_call_title" to m("Long call from an unknown number", "अनजान नंबर से लंबी कॉल", "अनोळखी नंबरवरून लांब कॉल"),
        "disclaimer" to m("Kavach warns; you decide. Kavach is not the police, the government or your bank.", "कवच चेतावनी देता है; फ़ैसला आपका है। कवच पुलिस, सरकार या बैंक नहीं है।", "कवच इशारा देते; निर्णय तुमचा. कवच पोलीस, सरकार किंवा बँक नाही."),
    )

    private fun m(en: String, hi: String, mr: String) = mapOf("en" to en, "hi" to hi, "mr" to mr)

    fun get(key: String, lang: String): String = t[key]?.let { it[lang] ?: it["en"] } ?: key
}
