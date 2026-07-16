"""
Production‑grade configuration manager with atomic writes, env overrides,
thread safety, and configurable paths.
"""

from __future__ import annotations

import logging
import os
import threading
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: Dict[str, Any] = {
    "security": {
        "watch_zones": [],
        "threat_threshold": 75,
    },
    "api_keys": {},
    "settings": {
        "default_service": "ip-api",
    },
}


class ConfigManager:
    """
    Manages application configuration stored in a YAML file.

    Environment variables can override or extend settings without touching the file:
        - IPGEO_HOME           : override base directory (default: ~/.ipgeo)
        - IPGEO_REPORTS        : override reports directory (default: <base>/reports)
        - IPGEO_API_<SERVICE>  : override API key for a service, e.g.
                                 IPGEO_API_IPSTACK=key123
    """

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        reports_dir: Optional[Path] = None,
    ):
        self.BASE_DIR: Path = base_dir or Path(
            os.getenv("IPGEO_HOME", str(Path.home() / ".ipgeo"))
        )
        self.CACHE_DB: Path = self.BASE_DIR / "intel_cache.db"
        self.config_path: Path = self.BASE_DIR / "config.yaml"

        self.REPORTS_DIR: Path = reports_dir or Path(
            os.getenv("IPGEO_REPORTS", str(self.BASE_DIR / "reports"))
        )

        self.BASE_DIR.mkdir(parents=True, exist_ok=True)
        self.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        # MaxMind credentials (load from env if present)
        self.maxmind_credentials: tuple = (
            os.getenv("MAXMIND_ACCOUNT_ID"),
            os.getenv("MAXMIND_LICENSE_KEY"),
        )

        self._lock = threading.Lock()
        self.config: Dict[str, Any] = self._load()

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        with self._lock:
            return self.config.get(section, {}).get(key, fallback)

    def get_api_key(self, service: str) -> Optional[str]:
        env_key = f"IPGEO_API_{service.upper()}"
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value
        with self._lock:
            return self.config.get("api_keys", {}).get(service.lower())

    def get_maxmind_auth(self) -> tuple:
        """Return MaxMind credentials from environment or config."""
        return self.maxmind_credentials

    def set(self, section: str, key: str, value: Any) -> None:
        with self._lock:
            if section not in self.config:
                self.config[section] = {}
            self.config[section][key] = value

    def save(self) -> bool:
        with self._lock:
            try:
                tmp_fd, tmp_path = tempfile.mkstemp(
                    dir=str(self.BASE_DIR), prefix="config_", suffix=".tmp"
                )
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                    yaml.dump(self.config, f, default_flow_style=False)
                os.replace(tmp_path, self.config_path)
                logger.info("Configuration saved to %s", self.config_path)
                return True
            except Exception as exc:
                logger.error("Failed to save configuration: %s", exc)
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return False

    def reload(self) -> None:
        with self._lock:
            self.config = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return self._deepcopy_default()
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as exc:
            logger.warning(
                "Failed to parse config file %s: %s. Renaming to .broken and using defaults.",
                self.config_path, exc,
            )
            broken_path = self.config_path.with_suffix(".yaml.broken")
            try:
                self.config_path.rename(broken_path)
            except Exception as rename_exc:
                logger.error("Could not rename broken config: %s", rename_exc)
            return self._deepcopy_default()
        if not isinstance(data, dict):
            return self._deepcopy_default()
        merged = self._deepcopy_default()
        self._merge_dicts(merged, data)
        return merged

    @staticmethod
    def _deepcopy_default() -> Dict[str, Any]:
        return yaml.safe_load(yaml.dump(DEFAULT_CONFIG))

    @staticmethod
    def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> None:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigManager._merge_dicts(base[key], value)
            else:
                base[key] = value
