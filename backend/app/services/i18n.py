"""User-facing text in each launch language.

Written to be read aloud: short sentences, no jargon, never blaming the user.
English (en), Hindi (hi) and Marathi (mr) are complete; any other language
falls back to Hindi then English. Have a native writer review every string
before launch - these are first drafts.
"""

SUPPORTED = ("en", "hi", "mr")

T: dict[str, dict[str, str]] = {
    # ---- verdicts (F5) ----
    "verdict.safe": {
        "en": "✅ Looks safe. We did not find signs of a scam. If anyone asks for money, an OTP or a PIN, stop and check.",
        "hi": "✅ सुरक्षित लगता है। हमें धोखाधड़ी के संकेत नहीं मिले। अगर कोई पैसे, OTP या PIN माँगे, तो रुकें और जाँचें।",
        "mr": "✅ सुरक्षित वाटते. फसवणुकीची चिन्हे दिसली नाहीत. कोणी पैसे, OTP किंवा PIN मागितला तर थांबा आणि तपासा.",
    },
    "verdict.suspicious": {
        "en": "⚠️ Suspicious. Do not pay, click links or share OTP/PIN yet. Call your family or your bank on its official number first.",
        "hi": "⚠️ संदिग्ध है। अभी पैसे न भेजें, लिंक न खोलें, OTP/PIN न बताएं। पहले परिवार से या बैंक के असली नंबर पर बात करें।",
        "mr": "⚠️ संशयास्पद आहे. आत्ता पैसे पाठवू नका, लिंक उघडू नका, OTP/PIN सांगू नका. आधी कुटुंबाशी किंवा बँकेच्या अधिकृत नंबरवर बोला.",
    },
    "verdict.scam": {
        "en": "🛑 This is very likely a SCAM. Do not pay or reply. If you already paid, call 1930 now.",
        "hi": "🛑 यह लगभग निश्चित रूप से धोखाधड़ी है। पैसे न भेजें, जवाब न दें। अगर पैसे भेज दिए हैं, तो अभी 1930 पर कॉल करें।",
        "mr": "🛑 ही बहुधा फसवणूक आहे. पैसे पाठवू नका, उत्तर देऊ नका. पैसे पाठवले असतील तर लगेच 1930 वर कॉल करा.",
    },
    "verdict.why": {"en": "Why: {reason}", "hi": "कारण: {reason}", "mr": "कारण: {reason}"},
    "disclaimer": {
        "en": "Kavach warns; you decide. We are not the police or your bank.",
        "hi": "कवच चेतावनी देता है; फ़ैसला आपका है। हम पुलिस या बैंक नहीं हैं।",
        "mr": "कवच इशारा देते; निर्णय तुमचा. आम्ही पोलीस किंवा बँक नाही.",
    },
    # ---- call warnings (F2) ----
    "call.warn": {
        "en": "Careful. This call may be a scam. Real police and banks never ask for money on a call.",
        "hi": "सावधान। यह कॉल धोखाधड़ी हो सकती है। असली पुलिस या बैंक फ़ोन पर कभी पैसे नहीं माँगते।",
        "mr": "सावध. हा कॉल फसवणुकीचा असू शकतो. खरे पोलीस किंवा बँक फोनवर कधीही पैसे मागत नाहीत.",
    },
    "call.caution": {
        "en": "Unknown caller. If they ask for money, an OTP or to keep it secret, hang up.",
        "hi": "अनजान नंबर। अगर पैसे, OTP माँगें या बात छुपाने को कहें, तो फ़ोन काट दें।",
        "mr": "अनोळखी नंबर. पैसे, OTP मागितले किंवा गुप्त ठेवायला सांगितले तर फोन ठेवा.",
    },
    "call.safe": {"en": "", "hi": "", "mr": ""},
    "long_call.nudge": {
        "en": "You have been on this call for a long time. It is OK to hang up and call your family. Real officers never keep you on a call.",
        "hi": "आप काफ़ी देर से इस कॉल पर हैं। फ़ोन काटकर परिवार को कॉल करना ठीक है। असली अधिकारी आपको कॉल पर रोककर नहीं रखते।",
        "mr": "तुम्ही बराच वेळ या कॉलवर आहात. फोन ठेवून कुटुंबाला कॉल करणे योग्य आहे. खरे अधिकारी तुम्हाला कॉलवर थांबवून ठेवत नाहीत.",
    },
    # ---- checklist (F3) ----
    "check.q.stay_on_call": {"en": "Are they asking you to stay on the call or video call?", "hi": "क्या वे आपको कॉल या वीडियो कॉल पर बने रहने को कह रहे हैं?", "mr": "ते तुम्हाला कॉल किंवा व्हिडिओ कॉलवर थांबायला सांगत आहेत का?"},
    "check.q.secret": {"en": "Are they telling you to keep it secret from family or the bank?", "hi": "क्या वे कह रहे हैं कि परिवार या बैंक को न बताएं?", "mr": "ते कुटुंबाला किंवा बँकेला सांगू नका असे म्हणत आहेत का?"},
    "check.q.pay": {"en": "Are they asking you to pay, transfer money or share an OTP or PIN?", "hi": "क्या वे पैसे भेजने, ट्रांसफ़र करने या OTP/PIN बताने को कह रहे हैं?", "mr": "ते पैसे पाठवायला, ट्रान्सफर करायला किंवा OTP/PIN सांगायला सांगत आहेत का?"},
    "check.q.authority": {"en": "Do they say they are police, CBI, customs, a court or the bank?", "hi": "क्या वे ख़ुद को पुलिस, CBI, कस्टम, कोर्ट या बैंक बता रहे हैं?", "mr": "ते स्वतःला पोलीस, CBI, कस्टम्स, कोर्ट किंवा बँक म्हणवत आहेत का?"},
    "check.q.app": {"en": "Are they asking you to install an app or open a link?", "hi": "क्या वे कोई ऐप डाउनलोड करने या लिंक खोलने को कह रहे हैं?", "mr": "ते एखादे ॲप इंस्टॉल करायला किंवा लिंक उघडायला सांगत आहेत का?"},
    "check.stop": {
        "en": "Stop. This is how scams work. Hang up now - it is safe to do so. We are calling your family.",
        "hi": "रुकिए। धोखेबाज़ ऐसे ही करते हैं। अभी फ़ोन काट दें - ऐसा करना बिल्कुल ठीक है। हम आपके परिवार को बता रहे हैं।",
        "mr": "थांबा. फसवणूक अशीच होते. आत्ता फोन ठेवा - हे पूर्णपणे योग्य आहे. आम्ही तुमच्या कुटुंबाला कळवत आहोत.",
    },
    "check.ok": {
        "en": "No warning signs from your answers. Still, never share an OTP or PIN. You can check again anytime.",
        "hi": "आपके जवाबों में ख़तरे के संकेत नहीं हैं। फिर भी OTP या PIN कभी न बताएं। आप कभी भी फिर से जाँच सकते हैं।",
        "mr": "तुमच्या उत्तरांत धोक्याची चिन्हे नाहीत. तरीही OTP किंवा PIN कधीही सांगू नका. कधीही पुन्हा तपासू शकता.",
    },
    # ---- WhatsApp bot ----
    "wa.welcome": {
        "en": "Namaste! I am Kavach. Forward me any message, link, screenshot or phone number and I will tell you if it looks like a scam.",
        "hi": "नमस्ते! मैं कवच हूँ। कोई भी मैसेज, लिंक, स्क्रीनशॉट या फ़ोन नंबर मुझे फ़ॉरवर्ड करें, मैं बताऊँगा कि यह धोखाधड़ी तो नहीं।",
        "mr": "नमस्कार! मी कवच. कोणताही मेसेज, लिंक, स्क्रीनशॉट किंवा फोन नंबर मला फॉरवर्ड करा, मी सांगेन की ही फसवणूक आहे का.",
    },
    "wa.unsupported": {
        "en": "I can check text, links, phone numbers and screenshots. Please forward one of those.",
        "hi": "मैं टेक्स्ट, लिंक, फ़ोन नंबर और स्क्रीनशॉट जाँच सकता हूँ। कृपया इनमें से कुछ भेजें।",
        "mr": "मी मजकूर, लिंक, फोन नंबर आणि स्क्रीनशॉट तपासू शकतो. कृपया यापैकी काही पाठवा.",
    },
    # ---- guardian alerts (WhatsApp template body params are built from these) ----
    "alert.call_warning": {"en": "{senior} just got a call from {number}, which looks like a scam.", "hi": "{senior} को अभी {number} से कॉल आई, जो धोखाधड़ी लगती है।", "mr": "{senior} यांना आत्ता {number} वरून कॉल आला, जो फसवणुकीचा वाटतो."},
    "alert.help_pressed": {"en": "{senior} pressed 'Am I being scammed?'. Please call them now.", "hi": "{senior} ने 'क्या मेरे साथ धोखा हो रहा है?' दबाया। कृपया अभी उन्हें कॉल करें।", "mr": "{senior} यांनी 'माझी फसवणूक होत आहे का?' दाबले. कृपया आत्ता त्यांना कॉल करा."},
    "alert.checklist_yes": {"en": "{senior} answered YES to scam warning signs: {detail}. Call them now.", "hi": "{senior} ने धोखाधड़ी के संकेतों पर 'हाँ' कहा: {detail}। अभी कॉल करें।", "mr": "{senior} यांनी फसवणुकीच्या चिन्हांना 'हो' म्हटले: {detail}. आत्ता कॉल करा."},
    "alert.message_scam": {"en": "{senior} checked a message that looks like a scam ({detail}).", "hi": "{senior} ने एक मैसेज जाँचा जो धोखाधड़ी लगता है ({detail})।", "mr": "{senior} यांनी तपासलेला मेसेज फसवणुकीचा वाटतो ({detail})."},
    "alert.long_call": {"en": "{senior} has been on a call with unknown number {number} for {minutes} minutes. Digital-arrest scams keep people on long calls. Please call them.", "hi": "{senior} {minutes} मिनट से अनजान नंबर {number} की कॉल पर हैं। 'डिजिटल अरेस्ट' ठगी में लंबी कॉल होती है। कृपया उन्हें कॉल करें।", "mr": "{senior} {minutes} मिनिटे अनोळखी नंबर {number} वरील कॉलवर आहेत. 'डिजिटल अरेस्ट' फसवणुकीत लांब कॉल असतात. कृपया त्यांना कॉल करा."},
    "alert.transfer_hold": {"en": "{bank} has paused a transfer of ₹{amount} from {senior} to {payee}. Open Kavach to approve or decline within {minutes} minutes. Call {senior} first.", "hi": "{bank} ने {senior} के ₹{amount} के {payee} को ट्रांसफ़र को रोका है। {minutes} मिनट में कवच खोलकर मंज़ूर या अस्वीकार करें। पहले {senior} को कॉल करें।", "mr": "{bank} ने {senior} यांचे {payee} ला ₹{amount} चे ट्रान्सफर थांबवले आहे. {minutes} मिनिटांत कवच उघडून मंजूर किंवा नामंजूर करा. आधी {senior} यांना कॉल करा."},
}

REASONS: dict[str, dict[str, str]] = {
    "scam_list": {"en": "this number is on our scam list", "hi": "यह नंबर हमारी धोखाधड़ी सूची में है", "mr": "हा नंबर आमच्या फसवणूक यादीत आहे"},
    "user_reports": {"en": "several people reported this number as a scam", "hi": "कई लोगों ने इस नंबर को धोखाधड़ी बताया है", "mr": "अनेकांनी हा नंबर फसवणुकीचा म्हणून कळवला आहे"},
    "international": {"en": "this is an international number", "hi": "यह विदेशी नंबर है", "mr": "हा परदेशी नंबर आहे"},
    "malformed_indian": {"en": "the number looks faked", "hi": "नंबर नकली लगता है", "mr": "नंबर बनावट वाटतो"},
    "repeat_unknown": {"en": "this unknown number has called many times", "hi": "इस अनजान नंबर से कई बार कॉल आई है", "mr": "या अनोळखी नंबरवरून अनेकदा कॉल आला आहे"},
    "telemarketing_series": {"en": "this is a marketing number", "hi": "यह मार्केटिंग नंबर है", "mr": "हा मार्केटिंग नंबर आहे"},
    "hidden_number": {"en": "the caller's number is hidden", "hi": "कॉल करने वाले का नंबर छुपा है", "mr": "कॉल करणाऱ्याचा नंबर लपवलेला आहे"},
    "unknown": {"en": "this number is not in your contacts", "hi": "यह नंबर आपके कॉन्टैक्ट में नहीं है", "mr": "हा नंबर तुमच्या संपर्कात नाही"},
    "digital_arrest": {"en": "it uses a 'digital arrest' / police threat script", "hi": "इसमें 'डिजिटल अरेस्ट' या पुलिस की धमकी है", "mr": "यात 'डिजिटल अरेस्ट' किंवा पोलिसांची धमकी आहे"},
    "courier_customs": {"en": "it uses a fake courier/customs story", "hi": "इसमें नकली कूरियर/कस्टम की कहानी है", "mr": "यात बनावट कुरिअर/कस्टम्सची गोष्ट आहे"},
    "kyc_block": {"en": "it threatens to block your account or KYC", "hi": "इसमें खाता या KYC बंद होने की धमकी है", "mr": "यात खाते किंवा KYC बंद होण्याची धमकी आहे"},
    "electricity": {"en": "it threatens to cut your electricity", "hi": "इसमें बिजली काटने की धमकी है", "mr": "यात वीज कापण्याची धमकी आहे"},
    "investment": {"en": "it promises unrealistic investment returns", "hi": "इसमें निवेश पर असंभव मुनाफ़े का वादा है", "mr": "यात गुंतवणुकीवर अशक्य नफ्याचे वचन आहे"},
    "task_job": {"en": "it is a fake part-time job offer", "hi": "यह नकली पार्ट-टाइम नौकरी का ऑफ़र है", "mr": "ही बनावट पार्ट-टाइम नोकरीची ऑफर आहे"},
    "lottery_prize": {"en": "it claims you won a prize or lottery", "hi": "इसमें लॉटरी या इनाम जीतने की बात है", "mr": "यात लॉटरी किंवा बक्षीस जिंकल्याचे सांगितले आहे"},
    "refund_upi": {"en": "it asks for your UPI PIN or a QR scan to 'receive' money", "hi": "पैसे 'पाने' के लिए UPI PIN या QR स्कैन माँगा गया है", "mr": "पैसे 'मिळवण्यासाठी' UPI PIN किंवा QR स्कॅन मागितला आहे"},
    "otp_request": {"en": "it asks you to share an OTP", "hi": "इसमें OTP माँगा गया है", "mr": "यात OTP मागितला आहे"},
    "remote_app": {"en": "it asks you to install an app or APK", "hi": "इसमें ऐप या APK डाउनलोड करने को कहा गया है", "mr": "यात ॲप किंवा APK इंस्टॉल करायला सांगितले आहे"},
    "secrecy_urgency": {"en": "it pressures you to act fast and keep it secret", "hi": "इसमें जल्दी करने और बात छुपाने का दबाव है", "mr": "यात घाई करण्याचा आणि गुप्त ठेवण्याचा दबाव आहे"},
    "impersonation": {"en": "it claims to be from a government office or bank", "hi": "यह किसी सरकारी विभाग या बैंक के नाम से है", "mr": "हे सरकारी कार्यालय किंवा बँकेच्या नावाने आहे"},
    "pay_to_verify": {"en": "it asks you to pay to 'verify' or into a 'safe account'", "hi": "इसमें 'जाँच' या 'सुरक्षित खाते' के लिए पैसे माँगे गए हैं", "mr": "यात 'पडताळणी' किंवा 'सुरक्षित खात्या'साठी पैसे मागितले आहेत"},
    "family_emergency": {"en": "it claims a family emergency and asks for money", "hi": "इसमें परिवार की आपात स्थिति बताकर पैसे माँगे गए हैं", "mr": "यात कुटुंबाची आणीबाणी सांगून पैसे मागितले आहेत"},
    "ip_url": {"en": "the link hides its real address", "hi": "लिंक का असली पता छुपा है", "mr": "लिंकचा खरा पत्ता लपवलेला आहे"},
    "punycode": {"en": "the link uses look-alike letters", "hi": "लिंक में मिलते-जुलते अक्षर हैं", "mr": "लिंकमध्ये सारखी दिसणारी अक्षरे आहेत"},
    "shortener": {"en": "the link is shortened to hide where it goes", "hi": "लिंक छोटा करके असली जगह छुपाई गई है", "mr": "लिंक लहान करून खरी जागा लपवली आहे"},
    "risky_tld": {"en": "the website address is of a type often used by scammers", "hi": "वेबसाइट का पता ठगों में आम है", "mr": "वेबसाइटचा पत्ता फसवणुकीत नेहमी वापरला जातो"},
    "apk_download": {"en": "the link downloads an app file (APK)", "hi": "लिंक से ऐप फ़ाइल (APK) डाउनलोड होती है", "mr": "लिंकवरून ॲप फाइल (APK) डाउनलोड होते"},
    "brand_lookalike": {"en": "the link pretends to be a bank or company but is not its real website", "hi": "लिंक बैंक या कंपनी की नकल है, असली वेबसाइट नहीं", "mr": "लिंक बँक किंवा कंपनीची नक्कल आहे, खरी वेबसाइट नाही"},
    "sim_block": {"en": "it threatens to block your SIM or number", "hi": "इसमें सिम या नंबर बंद करने की धमकी है", "mr": "यात सिम किंवा नंबर बंद करण्याची धमकी आहे"},
    "money_request": {"en": "it asks you to send money", "hi": "इसमें पैसे भेजने को कहा गया है", "mr": "यात पैसे पाठवायला सांगितले आहे"},
    "new_number": {"en": "someone with a 'new number' is asking for money", "hi": "'नए नंबर' से कोई पैसे माँग रहा है", "mr": "'नवीन नंबर' वरून कोणी पैसे मागत आहे"},
    "too_good_offer": {"en": "the offer sounds too good to be true", "hi": "ऑफ़र सच होने के लिए बहुत अच्छा लगता है", "mr": "ऑफर खरी असण्याइतकी चांगली वाटत नाही"},
    "no_signals": {"en": "we found no warning signs", "hi": "कोई ख़तरे का संकेत नहीं मिला", "mr": "धोक्याचे कोणतेही चिन्ह मिळाले नाही"},
}


def lang_of(lang: str | None) -> str:
    return lang if lang in SUPPORTED else "hi"


def t(key: str, lang: str | None = "hi", **kw) -> str:
    entry = T[key]
    text = entry.get(lang_of(lang)) or entry["en"]
    return text.format(**kw) if kw else text


def reason(code: str, lang: str | None = "hi") -> str:
    entry = REASONS.get(code)
    if not entry:
        return code
    return entry.get(lang_of(lang)) or entry["en"]
