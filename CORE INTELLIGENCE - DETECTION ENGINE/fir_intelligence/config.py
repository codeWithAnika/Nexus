"""
Single source of truth for NVIDIA Nemotron NIM configuration.
Authoritatively loads .env variables into os.environ with force_reload=True.
"""

import os
from pathlib import Path
from typing import Dict, Optional


def load_env_file(env_path: Optional[Path] = None, force_reload: bool = True) -> Dict[str, str]:
    """
    Authoritatively loads .env file into os.environ.
    When force_reload=True, overrides existing os.environ keys so stale terminal vars do not take precedence.
    """
    if env_path is None:
        env_path = Path(__file__).parent.parent / ".env"

    loaded_vars: Dict[str, str] = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'").strip('"')
                    if key:
                        loaded_vars[key] = val
                        if force_reload or key not in os.environ:
                            os.environ[key] = val

    return loaded_vars


class NemotronConfig:
    """
    Configuration model for NVIDIA Nemotron NIM API connection.
    """

    def __init__(self, env_path: Optional[Path] = None):
        load_env_file(env_path=env_path, force_reload=True)

        self.api_key = os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY", "")
        self.base_url = os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.model = os.getenv("NVIDIA_NIM_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
        
        try:
            self.timeout = float(os.getenv("NVIDIA_NIM_TIMEOUT", "30"))
        except ValueError:
            self.timeout = 30.0

        env_enabled = os.getenv("NVIDIA_NIM_ENABLED", "true").lower() in ("true", "1", "yes")
        self.enabled = env_enabled

    def is_configured(self) -> bool:
        """Returns True if enabled and a non-empty API key is present."""
        return self.enabled and bool(self.api_key)
