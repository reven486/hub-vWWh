import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel


class AppConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8016
    debug: bool = False


class LLMConfig(BaseModel):
    model: str = "gpt-4.1-mini"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    max_tokens: int = 800
    temperature: float = 0.6


class GameConfig(BaseModel):
    max_turns: int = 12
    default_setup: str = "standard_7"
    data_dir: str = "data/matches"


class SQLiteConfig(BaseModel):
    db_path: str = "data/werewolf.db"


class Settings(BaseModel):
    app: AppConfig = AppConfig()
    llm: LLMConfig = LLMConfig()
    game: GameConfig = GameConfig()
    sqlite: SQLiteConfig = SQLiteConfig()


def _resolve_env(value: str) -> str:
    if value.startswith("${") and value.endswith("}"):
        return os.environ.get(value[2:-1], "")
    return value


def _resolve_dict(data: dict) -> dict:
    result: dict = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = _resolve_dict(value)
        elif isinstance(value, str):
            result[key] = _resolve_env(value)
        else:
            result[key] = value
    return result


@lru_cache
def get_settings() -> Settings:
    config_path = Path(__file__).parent.parent.parent / "configs" / "config.yaml"
    if config_path.exists():
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        return Settings(**_resolve_dict(raw))
    return Settings()
