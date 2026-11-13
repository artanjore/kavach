"""Runtime configuration, read from environment variables.

Nothing secret has a default. In dev (KAVACH_ENV=dev) OTPs are returned in the
API response and WhatsApp/push messages are written to the outbox table
instead of being sent.
"""
import os
from dataclasses import dataclass, field


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    env: str = field(default_factory=lambda: _env("KAVACH_ENV", "dev"))
    database_url: str = field(default_factory=lambda: _env("DATABASE_URL", "sqlite:///./kavach.db"))

    # WhatsApp Cloud API
    wa_token: str = field(default_factory=lambda: _env("WHATSAPP_TOKEN"))
    wa_phone_number_id: str = field(default_factory=lambda: _env("WHATSAPP_PHONE_NUMBER_ID"))
    wa_verify_token: str = field(default_factory=lambda: _env("WHATSAPP_VERIFY_TOKEN", "dev-verify-token"))
    wa_app_secret: str = field(default_factory=lambda: _env("WHATSAPP_APP_SECRET"))
    wa_alert_template: str = field(default_factory=lambda: _env("WHATSAPP_ALERT_TEMPLATE", "kavach_guardian_alert"))
    wa_graph_version: str = field(default_factory=lambda: _env("WHATSAPP_GRAPH_VERSION", "v21.0"))

    # LLM classifier (optional: rules still work without it)
    anthropic_api_key: str = field(default_factory=lambda: _env("ANTHROPIC_API_KEY"))
    llm_model: str = field(default_factory=lambda: _env("KAVACH_LLM_MODEL", "claude-opus-5-5"))
    llm_enabled: bool = field(default_factory=lambda: _env("KAVACH_LLM_ENABLED", "1") == "1")

    # Bank partner API (v2)
    bank_api_keys: str = field(default_factory=lambda: _env("BANK_API_KEYS"))  # "bankcode:key,bankcode2:key2"
    hold_decision_minutes: int = field(default_factory=lambda: int(_env("HOLD_DECISION_MINUTES", "60")))
    guardian_approval_cooloff_hours: int = field(default_factory=lambda: int(_env("GUARDIAN_COOLOFF_HOURS", "24")))

    # Risk thresholds
    report_threshold: int = field(default_factory=lambda: int(_env("SCAM_REPORT_THRESHOLD", "3")))
    repeat_call_threshold: int = field(default_factory=lambda: int(_env("REPEAT_CALL_THRESHOLD", "3")))
    long_call_seconds: int = field(default_factory=lambda: int(_env("LONG_CALL_SECONDS", "600")))

    @property
    def is_dev(self) -> bool:
        return self.env == "dev"

    def bank_keys(self) -> dict[str, str]:
        out = {}
        for pair in filter(None, self.bank_api_keys.split(",")):
            code, _, key = pair.partition(":")
            out[key.strip()] = code.strip()
        if self.is_dev and not out:
            out["dev-bank-key"] = "DEVBANK"
        return out


settings = Settings()
