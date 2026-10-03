from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    """Used by the frontend to wake the server."""
    return {"status": "ok"}
