"""Configuration management."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
DEFAULT_INVESTIGATION_STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "investigations.sqlite3"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv_env(name: str) -> list[str]:
    raw = os.getenv(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw is not None else default


_load_dotenv(ENV_PATH)


@dataclass(frozen=True)
class Settings:
    investigation_store_path: str = os.getenv("INVESTIGATION_STORE_PATH", str(DEFAULT_INVESTIGATION_STORE_PATH))
    tinyfish_api_key: str = os.getenv("TINYFISH_API_KEY", "")
    tinyfish_base_url: str = os.getenv("TINYFISH_BASE_URL", "https://agent.tinyfish.ai")
    tinyfish_browser_profile: str = os.getenv("TINYFISH_BROWSER_PROFILE", "stealth")
    tinyfish_proxy_enabled: bool = _bool_env("TINYFISH_PROXY_ENABLED", False)
    tinyfish_proxy_country_code: str = os.getenv("TINYFISH_PROXY_COUNTRY_CODE", "SG")
    tinyfish_poll_interval_seconds: float = _float_env("TINYFISH_POLL_INTERVAL_SECONDS", 2.0)
    tinyfish_http_timeout_seconds: float = _float_env("TINYFISH_HTTP_TIMEOUT_SECONDS", 15.0)
    tinyfish_run_soft_timeout_seconds: float = _float_env("TINYFISH_RUN_SOFT_TIMEOUT_SECONDS", 300.0)
    tinyfish_run_hard_timeout_seconds: float = _float_env("TINYFISH_RUN_HARD_TIMEOUT_SECONDS", 1800.0)
    tinyfish_run_stall_timeout_seconds: float = _float_env("TINYFISH_RUN_STALL_TIMEOUT_SECONDS", 120.0)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
    openai_triage_model: str = os.getenv("OPENAI_TRIAGE_MODEL", "gpt-5-mini")
    openai_reasoning_model: str = os.getenv("OPENAI_REASONING_MODEL", "gpt-5-mini")
    openai_http_timeout_seconds: float = _float_env("OPENAI_HTTP_TIMEOUT_SECONDS", 30.0)
    openai_shortlist_limit: int = int(os.getenv("OPENAI_SHORTLIST_LIMIT", "6"))
    job_search_urls: list[str] = _csv_env("JOB_SEARCH_URLS")
    upload_dir: str = os.getenv("UPLOAD_DIR", "data/uploads")
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    log_path: str = os.getenv("LOG_PATH", "logs/job_matcher.log")




@dataclass(frozen=True)
class Settings:
    """Application settings."""
    backend_host: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_job_extraction_model: str = os.getenv("OPENAI_JOB_EXTRACTION_MODEL", "gpt-4")
    openai_triage_model: str = os.getenv("OPENAI_TRIAGE_MODEL", "gpt-4")
    openai_comparison_model: str = os.getenv("OPENAI_COMPARISON_MODEL", "gpt-4")
    openai_chatbot_model: str = os.getenv("OPENAI_CHATBOT_MODEL", "gpt-4")
    
    job_store_path: str = os.getenv("JOB_STORE_PATH", "data/job_matches.sqlite3")
    upload_dir: str = os.getenv("UPLOAD_DIR", "data/uploads")
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))
    
    indeed_api_key: str = os.getenv("INDEED_API_KEY", "")
    linkedin_api_key: str = os.getenv("LINKEDIN_API_KEY", "")
    
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    log_path: str = os.getenv("LOG_PATH", "logs/job_matcher.log")
    
    def __post_init__(self) -> None:
        object.__setattr__(self, "ecommerce_store_urls", _csv_env("ECOMMERCE_STORE_URLS"))

    @property
    def tinyfish_enabled(self) -> bool:
        return bool(self.tinyfish_api_key)

    @property
    def openai_enabled(self) -> bool:
        return bool(self.openai_api_key)


settings = Settings()