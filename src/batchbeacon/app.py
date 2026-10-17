"""Local preparation shell; no model, persistence or decision capability yet."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="BatchBeacon AI — preparation", docs_url=None, redoc_url=None)


@app.get("/healthz")
def health() -> dict[str, str]:
    """Cheap process health. Never advertise an unverified AI journey."""
    return {"process": "ok", "product": "not_ready", "mode": "local_preparation"}


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse("/prototype/")


app.mount(
    "/prototype",
    StaticFiles(directory=Path(__file__).resolve().parents[2] / "prototypes", html=True),
    name="prototype",
)
