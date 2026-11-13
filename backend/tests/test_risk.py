from app.risk.engine import assess_message
from app.risk.phone import normalize, shape_signals
from app.risk.urls import url_signals


def test_normalize():
    assert normalize("98765 43210") == "+919876543210"
    assert normalize("09876543210") == "+919876543210"
    assert normalize("+1 (415) 555-0100") == "+14155550100"
    assert normalize("1930") == "1930"


def test_shape():
    assert "international" in shape_signals("+447700900123")
    assert "malformed_indian" in shape_signals("+91 12345")
    assert "trai_1600_series" in shape_signals("1600123456")
    assert shape_signals("+919876543210") == []


def test_urls():
    assert "brand_lookalike" in url_signals("http://sbi-kyc-update.xyz/login")
    assert "risky_tld" in url_signals("http://sbi-kyc-update.xyz/login")
    assert "apk_download" in url_signals("http://45.12.88.10/x.apk")
    assert "ip_url" in url_signals("http://45.12.88.10/x.apk")
    assert "brand_lookalike" not in url_signals("https://www.onlinesbi.sbi/")
    assert "brand_lookalike" not in url_signals("https://www.hdfcbank.com/personal")
    assert "official_domain" in url_signals("https://incometax.gov.in")


def test_message_verdicts():
    assert assess_message(None, "You are under digital arrest, stay on video call", "en", use_llm=False).verdict == "scam"
    assert assess_message(None, "Your OTP is 123456. Do not share it with anyone.", "en", use_llm=False).verdict == "safe"
    assert assess_message(None, "Reached home safely, will call later", "hi", use_llm=False).verdict == "safe"


def test_reason_is_localised():
    a = assess_message(None, "Please install AnyDesk now", "hi", use_llm=False)
    assert a.verdict == "scam" and "ऐप" in a.reason


def test_bare_number_check():
    a = assess_message(None, "+44 7700 900123", "en", use_llm=False)
    assert a.verdict == "suspicious" and "international" in a.reason_codes
