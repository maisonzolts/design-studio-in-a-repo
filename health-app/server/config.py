"""Environment-only configuration for the sanitized health-coach API."""
from __future__ import annotations

import os
from pathlib import Path


def app_token() -> str:
    return os.environ.get("HEALTH_APP_TOKEN", "")


def health_dir() -> Path:
    return Path(os.environ.get("HEALTH_DATA_DIR", "./health")).resolve()
