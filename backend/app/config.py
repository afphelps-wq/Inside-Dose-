import os

DEFAULT_ORIGINS = "https://afphelps-wq.github.io,http://localhost:5173"


def allowed_origins() -> list[str]:
    raw = os.environ.get("ALLOWED_ORIGINS") or DEFAULT_ORIGINS
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
