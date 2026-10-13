"""Minimal health-coach API around the provenance validator.

The API deliberately excludes chat transcripts, wearable sync, deployment keys,
and personal history. Bring your own private HEALTH_DATA_DIR.
"""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException

from . import config

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from health_validate import validate_catalog  # noqa: E402

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


def require_token(token: str) -> None:
    expected = config.app_token()
    if not expected or token != expected:
        raise HTTPException(status_code=404)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/a/{token}/catalog/validate")
def validate(token: str) -> dict[str, object]:
    require_token(token)
    errors = validate_catalog(config.health_dir())
    return {"ok": not errors, "errors": errors}
