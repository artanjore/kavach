"""Phone-number normalisation and number-shape signals for Indian calls."""
import re

_DIGITS = re.compile(r"\D")


def normalize(raw: str) -> str:
    """Return an E.164-ish string. Indian 10-digit mobiles become +91XXXXXXXXXX.

    Short codes and service numbers (e.g. 1930, 1600xxxxxx) are kept as digits.
    """
    raw = (raw or "").strip()
    has_plus = raw.startswith("+")
    digits = _DIGITS.sub("", raw)
    if not digits:
        return ""
    if has_plus:
        return "+" + digits
    if digits.startswith("00"):
        return "+" + digits[2:]
    if len(digits) == 10 and digits[0] in "6789":
        return "+91" + digits
    if len(digits) == 11 and digits.startswith("0") and digits[1] in "6789":
        return "+91" + digits[1:]
    if len(digits) == 12 and digits.startswith("91") and digits[2] in "6789":
        return "+" + digits
    return digits


def shape_signals(number: str) -> list[str]:
    """Signals from the number alone. Returns reason codes (see i18n.REASONS)."""
    n = normalize(number)
    signals: list[str] = []
    if not n:
        signals.append("hidden_number")
        return signals
    if n.startswith("+") and not n.startswith("+91"):
        signals.append("international")
    if n.startswith("+91"):
        rest = n[3:]
        # A real Indian mobile is exactly 10 digits starting 6-9. Anything else
        # arriving with a +91 prefix is a spoofing red flag.
        if not (len(rest) == 10 and rest[0] in "6789") and not rest.startswith("1600") and not rest.startswith("140"):
            signals.append("malformed_indian")
    bare = n[3:] if n.startswith("+91") else n
    if bare.startswith("140"):
        signals.append("telemarketing_series")
    if bare.startswith("1600"):
        # TRAI's 1600xx series is reserved for banks/financial institutions and
        # government service calls. A genuine-leaning signal.
        signals.append("trai_1600_series")
    return signals
