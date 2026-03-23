import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, TypeVar


T = TypeVar('T')


def _load_dotenv(env_path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value
    return values


def _cast_bool(value: str) -> bool:
    return value.strip().lower() in {'1', 'true', 'yes', 'y', 'on'}


def _read_setting(name: str, default: T, caster: Callable[[str], T], dotenv: Dict[str, str]) -> T:
    raw_value = os.getenv(name)
    if raw_value is None:
        raw_value = dotenv.get(name)
    if raw_value is None or raw_value == '':
        return default
    try:
        return caster(raw_value)
    except Exception:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    app_host: str
    app_port: int
    log_level: str
    default_top_k_matches: int
    knowledge_base_dir: str
    enable_llm: bool
    llm_api_base_url: str
    llm_api_key: str
    llm_model: str
    llm_timeout_seconds: float

    @classmethod
    def from_env(cls) -> 'Settings':
        dotenv = _load_dotenv(Path('.env'))
        return cls(
            app_name=_read_setting('APP_NAME', 'Career Planning Agent', str, dotenv),
            app_env=_read_setting('APP_ENV', 'dev', str, dotenv),
            app_host=_read_setting('APP_HOST', '127.0.0.1', str, dotenv),
            app_port=_read_setting('APP_PORT', 8000, int, dotenv),
            log_level=_read_setting('LOG_LEVEL', 'INFO', str, dotenv),
            default_top_k_matches=_read_setting('DEFAULT_TOP_K_MATCHES', 3, int, dotenv),
            knowledge_base_dir=_read_setting('KNOWLEDGE_BASE_DIR', 'data/knowledge_base', str, dotenv),
            enable_llm=_read_setting('ENABLE_LLM', False, _cast_bool, dotenv),
            llm_api_base_url=_read_setting('LLM_API_BASE_URL', '', str, dotenv),
            llm_api_key=_read_setting('LLM_API_KEY', '', str, dotenv),
            llm_model=_read_setting('LLM_MODEL', '', str, dotenv),
            llm_timeout_seconds=_read_setting('LLM_TIMEOUT_SECONDS', 30.0, float, dotenv),
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings.from_env()


def resolve_knowledge_base_dir() -> Path:
    return Path(get_settings().knowledge_base_dir)
