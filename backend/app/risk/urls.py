"""Offline URL reputation heuristics.

These run with no network calls. A hook for an external reputation service
(e.g. Google Safe Browsing) can be added in check_url_reputation_remote().
"""
import ipaddress
from urllib.parse import urlparse

SHORTENERS = {"bit.ly", "tinyurl.com", "t.ly", "is.gd", "cutt.ly", "rb.gy", "shorturl.at", "goo.gl", "ow.ly", "t.co", "tiny.cc", "rebrand.ly"}
RISKY_TLDS = {"xyz", "top", "icu", "online", "site", "live", "club", "shop", "buzz", "rest", "click", "link", "cc", "tk", "ml", "ga", "cf", "gq", "apk"}

# Brands scammers impersonate -> domains that legitimately belong to them.
BRANDS = {
    "sbi": {"sbi.co.in", "onlinesbi.sbi", "sbi.bank.in", "onlinesbi.com"},
    "hdfc": {"hdfcbank.com", "hdfc.bank.in", "hdfc.com"},
    "icici": {"icicibank.com", "icici.bank.in"},
    "axis": {"axisbank.com", "axis.bank.in"},
    "kotak": {"kotak.com", "kotak.bank.in"},
    "pnb": {"pnbindia.in", "pnb.bank.in"},
    "rbi": {"rbi.org.in"},
    "incometax": {"incometax.gov.in"},
    "indiapost": {"indiapost.gov.in"},
    "fedex": {"fedex.com"},
    "bluedart": {"bluedart.com"},
    "paytm": {"paytm.com"},
    "phonepe": {"phonepe.com"},
    "uidai": {"uidai.gov.in"},
    "epfo": {"epfindia.gov.in"},
    "npci": {"npci.org.in"},
}
OFFICIAL_SUFFIXES = (".gov.in", ".nic.in", ".bank.in")


def _host(url: str) -> str:
    if not url.lower().startswith(("http://", "https://")):
        url = "http://" + url
    try:
        return (urlparse(url).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""


def _registrable(host: str) -> str:
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in {"co", "gov", "nic", "org", "bank", "net", "ac"} and parts[-1] == "in":
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def url_signals(url: str) -> list[str]:
    host = _host(url)
    if not host:
        return ["bad_url"]
    signals: list[str] = []
    try:
        ipaddress.ip_address(host)
        signals.append("ip_url")
    except ValueError:
        pass
    if host.startswith("xn--") or ".xn--" in host:
        signals.append("punycode")
    if host in SHORTENERS:
        signals.append("shortener")
    if host.rsplit(".", 1)[-1] in RISKY_TLDS:
        signals.append("risky_tld")
    if url.lower().split("?")[0].endswith(".apk"):
        signals.append("apk_download")
    reg = _registrable(host)
    compact = host.replace("-", "").replace(".", "")
    for brand, legit in BRANDS.items():
        if brand in compact and reg not in legit and not any(host == d or host.endswith("." + d) for d in legit):
            signals.append("brand_lookalike")
            break
    if host.endswith(OFFICIAL_SUFFIXES):
        signals = [s for s in signals if s != "brand_lookalike"]
        signals.append("official_domain")
    return signals


URL_SIGNAL_WEIGHTS = {"ip_url": 3, "punycode": 3, "shortener": 3, "risky_tld": 2, "apk_download": 5, "brand_lookalike": 4, "bad_url": 1, "official_domain": -2}
