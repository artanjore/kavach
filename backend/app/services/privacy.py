"""Itemised privacy notice (DPDP-style), designed to be read aloud by the app.

DRAFT - must be reviewed by an Indian privacy lawyer and a native-language
writer before launch.
"""
from .i18n import lang_of

NOTICE_VERSION = "2026-11-draft1"

PURPOSES = ("core_protection", "guardian_sharing", "whatsapp_alerts", "message_check")

_ITEMS = {
    "en": [
        ("What we collect", "Your phone number and language. For calls we warn you about: the caller's number, time and length. Messages you choose to forward to us."),
        ("What we never collect", "We never record calls, read your SMS, upload your contacts, or ask for bank passwords or PINs."),
        ("Why", "To warn you about scam calls and messages, and to alert the family members you choose."),
        ("Your family", "You decide what each family member can see. You can remove anyone at any time."),
        ("Your rights", "You can see, download or delete your data from the app, and withdraw consent as easily as you gave it."),
        ("How long", "Flagged-call and message records are deleted after 12 months."),
        ("Complaints", "Grievance officer: grievance@kavach.example (to be replaced). You can also complain to the Data Protection Board of India."),
    ],
    "hi": [
        ("हम क्या लेते हैं", "आपका फ़ोन नंबर और भाषा। जिन कॉल पर हम चेतावनी देते हैं: कॉल करने वाले का नंबर, समय और अवधि। जो मैसेज आप ख़ुद हमें भेजते हैं।"),
        ("हम कभी नहीं लेते", "हम कभी कॉल रिकॉर्ड नहीं करते, आपके SMS नहीं पढ़ते, कॉन्टैक्ट अपलोड नहीं करते, और बैंक पासवर्ड या PIN नहीं माँगते।"),
        ("क्यों", "आपको धोखाधड़ी वाली कॉल और मैसेज से सावधान करने के लिए, और आपके चुने हुए परिवारजनों को सूचना देने के लिए।"),
        ("आपका परिवार", "हर परिवारजन क्या देख सकता है, यह आप तय करते हैं। आप किसी को भी कभी भी हटा सकते हैं।"),
        ("आपके अधिकार", "आप ऐप से अपना डेटा देख, डाउनलोड या मिटा सकते हैं, और सहमति उतनी ही आसानी से वापस ले सकते हैं जितनी आसानी से दी थी।"),
        ("कितने समय तक", "चेतावनी वाली कॉल और मैसेज का रिकॉर्ड 12 महीने बाद मिटा दिया जाता है।"),
        ("शिकायत", "शिकायत अधिकारी: grievance@kavach.example (बदला जाएगा)। आप डेटा प्रोटेक्शन बोर्ड ऑफ़ इंडिया में भी शिकायत कर सकते हैं।"),
    ],
    "mr": [
        ("आम्ही काय घेतो", "तुमचा फोन नंबर आणि भाषा. ज्या कॉलबद्दल आम्ही इशारा देतो: कॉल करणाऱ्याचा नंबर, वेळ आणि कालावधी. तुम्ही स्वतः पाठवलेले मेसेज."),
        ("आम्ही कधीही घेत नाही", "आम्ही कधीही कॉल रेकॉर्ड करत नाही, SMS वाचत नाही, संपर्क अपलोड करत नाही, किंवा बँक पासवर्ड/PIN मागत नाही."),
        ("का", "फसवणुकीचे कॉल आणि मेसेजबद्दल तुम्हाला सावध करण्यासाठी, आणि तुम्ही निवडलेल्या कुटुंबीयांना कळवण्यासाठी."),
        ("तुमचे कुटुंब", "प्रत्येक कुटुंबीय काय पाहू शकतो हे तुम्ही ठरवता. कोणालाही कधीही काढू शकता."),
        ("तुमचे अधिकार", "ॲपमधून तुमचा डेटा पाहू, डाउनलोड किंवा हटवू शकता, आणि संमती दिली तितक्याच सहजपणे मागे घेऊ शकता."),
        ("किती काळ", "इशारा दिलेल्या कॉल आणि मेसेजच्या नोंदी 12 महिन्यांनंतर हटवल्या जातात."),
        ("तक्रार", "तक्रार अधिकारी: grievance@kavach.example (बदलले जाईल). डेटा प्रोटेक्शन बोर्ड ऑफ इंडियाकडेही तक्रार करू शकता."),
    ],
}


def notice(lang: str) -> dict:
    lang = lang_of(lang)
    return {"version": NOTICE_VERSION, "language": lang, "purposes": list(PURPOSES),
            "items": [{"title": a, "text": b} for a, b in _ITEMS[lang]]}
