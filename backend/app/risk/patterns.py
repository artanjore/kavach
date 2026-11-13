"""Rule patterns for Indian scam scripts (English, Hinglish, Hindi in Devanagari).

Each category has a list of regexes and a weight. Matches add up; the total
decides the rules-only verdict. Seed list - extend it weekly from logged
verdicts (see scripts/review_verdicts.py).
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    key: str
    weight: int
    patterns: tuple[re.Pattern, ...]
    negatives: tuple[re.Pattern, ...] = ()

    def matches(self, text: str) -> bool:
        return any(p.search(text) for p in self.patterns) and not any(n.search(text) for n in self.negatives)


def _c(key: str, weight: int, *pats: str, negatives: tuple[str, ...] = ()) -> Category:
    return Category(key, weight, tuple(re.compile(p, re.IGNORECASE) for p in pats),
                    tuple(re.compile(n, re.IGNORECASE) for n in negatives))


# Weight guide: 6+ = a scam on its own; 3-5 = suspicious alone, scam with one more signal.


CATEGORIES: tuple[Category, ...] = (
    _c("digital_arrest", 6,
       r"digital(ly)?\s*arrest", r"\b(cbi|ncb|ed|enforcement directorate|narcotics|crime branch|cyber\s*cell)\b.*\b(case|warrant|arrest|fir)\b",
       r"\b(arrest|warrant)\b.*\b(video call|skype|stay on (the )?call)\b", r"money\s*launder", r"\bfir\b.*\byour (aadhaar|name|number)\b",
       r"डिजिटल\s*अरेस्ट", r"गिरफ्तार", r"मनी\s*लॉन्ड्रिंग", r"(sim|aadhaar).*(misuse|illegal|band|block).*(police|case)"),
    _c("courier_customs", 4,
       r"\b(parcel|courier|fedex|dhl|package)\b.*\b(drugs?|mdma|narcotic|seized|customs|illegal|passport)\b",
       r"customs\s*(duty|clearance|department).*\b(pay|fee)\b", r"पार्सल.*(ड्रग|कस्टम)"),
    _c("kyc_block", 4,
       r"\b(kyc|pan|aadhaar)\b.*\b(expir|updat|block|suspend|deactivat|band)\w*", r"account\s*(will be\s*)?(blocked|suspended|frozen|closed)",
       r"(update|link)\s+your\s+(pan|kyc)", r"केवाईसी", r"खाता\s*(बंद|ब्लॉक)"),
    _c("electricity", 6, r"electricity.*(disconnect|cut).*(tonight|today|\d+\s*(pm|am))", r"बिजली.*(कट|काट)"),
    _c("investment", 6,
       r"\b(guaranteed|assured|fixed)\s+(returns?|profit)", r"\b\d{2,3}\s*%\s*(returns?|profit|monthly|daily)", r"\b(stock|ipo|trading)\s+(tips?|group|vip)\b",
       r"\bdouble\s+your\s+money\b", r"\b(crypto|usdt|forex)\b.*\b(profit|returns?|invest)", r"पैसा\s*डबल"),
    _c("task_job", 6, r"work\s*from\s*home.*(₹|rs\.?|inr)\s*\d", r"\b(lik|rat|review)\w*\s+(youtube|google|hotel)\w*.*\b(earn|pay|₹)", r"\bearn\b.*\b(daily|per (review|task|like))\b.*\b(lik|rat|review)", r"part[\s-]*time\s+job.*daily"),
    _c("lottery_prize", 4, r"\b(lottery|lucky draw|kbc|jackpot|prize|you have won|winner)\b", r"लॉटरी", r"इनाम"),
    _c("refund_upi", 6,
       r"\b(enter|share)\b.*\b(upi\s*)?pin\b.*\b(receive|get|refund)", r"\bcollect\s+request\b", r"scan.*qr.*(receive|refund|get money)", r"refund.*(scan|pin|link)"),
    _c("otp_request", 6, r"\b(share|tell|send|forward|read out)\b.*\botp\b", r"\botp\b.*\b(share|tell|bata)", r"ओटीपी.*(बताएं|बताओ|भेजें)",
       # Genuine OTP SMS say "do not share"; don't flag those.
       negatives=(r"(do not|don'?t|never)\s+share", r"never asks? for (your )?otp")),
    _c("remote_app", 6, r"\b(anydesk|teamviewer|quicksupport|rustdesk|screen\s*share)\b", r"\.apk\b", r"install\s+(this\s+)?app.*(link|apk)"),
    _c("secrecy_urgency", 2,
       r"(don'?t|do not)\s+(tell|inform)\s+(anyone|family|bank)", r"keep\s+(this\s+)?(secret|confidential)", r"\bimmediately\b|\b(within|in)\s+\d+\s*(min|hour)", r"\burgent(ly)?\b", r"किसी\s*को\s*(मत|न)\s*बताएं"),
    _c("impersonation", 2, r"\b(rbi|trai|income tax|police|customs|sbi|government of india|supreme court)\b.*\b(officer|department|notice)\b"),
    _c("pay_to_verify", 6, r"\b(pay|transfer|deposit)\b.*\b(verify|verification|safe account|rbi account|security deposit|clear your name)\b", r"सुरक्षित\s*खाते"),
    _c("sim_block", 6, r"\b(mobile|sim|number|phone)\b.*\b(blocked|disconnected|suspended|deactivated)\b.*\b(trai|illegal|police|dot)\b",
       r"\btrai\b.*\b(block|disconnect|officer)"),
    _c("money_request", 2, r"\b(pay|send|transfer|deposit)\b.*(₹|\brs\.?\s*\d|\binr\b|\bmoney\b|\bfee\b)"),
    _c("new_number", 3, r"(lost my phone|new number|changed my number|my other number).*(send|transfer|₹|money|pay)"),
    _c("too_good_offer", 3, r"\bloan\b.*\b(without documents|0\s*% interest|instant approval|no cibil)", r"\b(policy|insurance)\b.*\b(bonus|maturity amount|refund)\b",
       r"\b(free|claim)\b.*\b(gift|cashback|voucher)\b"),
    _c("family_emergency", 3, r"\b(your (son|daughter|grandson|granddaughter))\b.*\b(accident|arrested|hospital)\b.*\b(send|pay|money)\b"),
)

URL_RE = re.compile(r"(https?://[^\s<>\"']+|www\.[^\s<>\"']+|\b[a-z0-9-]+\.(?:in|com|xyz|top|info|online|site|live|club|icu|shop|apk|link|ly|cc)\b(?:/[^\s]*)?)", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s-]{8,14}\d)(?!\d)")
