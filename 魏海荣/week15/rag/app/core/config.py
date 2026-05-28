import os
from pathlib import Path
from typing import Optional
import yaml


class Config:
    _instance: Optional["Config"] = None
    _config: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        config_path = Path(__file__).parent.parent.parent / "configs" / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    def _resolve_env_vars(self, value):
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.getenv(env_var, "")
        return value

    def _process_config(self, config: dict) -> dict:
        result = {}
        for key, value in config.items():
            if isinstance(value, dict):
                result[key] = self._process_config(value)
            else:
                result[key] = self._resolve_env_vars(value)
        return result

    @property
    def app(self) -> dict:
        return self._config.get("app", {})

    @property
    def models(self) -> dict:
        return self._process_config(self._config.get("models", {}))

    @property
    def mineru(self) -> dict:
        return self._config.get("mineru", {})

    @property
    def database(self) -> dict:
        return self._config.get("database", {})

    @property
    def milvus(self) -> dict:
        return self._config.get("milvus", {})

    @property
    def kafka(self) -> dict:
        return self._config.get("kafka", {})


config = Config()
