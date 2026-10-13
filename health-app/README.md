# Sanitized health-coach API

This optional local API exposes the catalog validator without bundling private health data.

```bash
python -m venv .venv
.venv/bin/pip install -r health-app/requirements.txt
export HEALTH_APP_TOKEN='<RANDOM_LOCAL_SECRET>'
export HEALTH_DATA_DIR='<PRIVATE_HEALTH_DIR>'
cd health-app
../.venv/bin/uvicorn server.main:app --host 127.0.0.1 --port 8000
```

`GET /healthz` is public. `GET /a/<token>/catalog/validate` is capability-token protected. Do not expose this service publicly without adding production authentication, TLS, rate limits, and a privacy review.
