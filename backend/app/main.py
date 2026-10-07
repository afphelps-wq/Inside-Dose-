from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.config import allowed_origins
from backend.app.routers import drugs, health, interactions, targets

ERROR_CODES = {
    404: "not_found",
    422: "bad_input",
    502: "upstream_failed",
    503: "database_unavailable",
}

app = FastAPI(title="Inside Dose API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(health.router)
app.include_router(drugs.router)
app.include_router(interactions.router)
app.include_router(targets.router)


def error_response(status: int, message: str) -> JSONResponse:
    code = ERROR_CODES.get(status, "error")
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(StarletteHTTPException)
async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Something went wrong."
    if exc.status_code == 404 and message == "Not Found":
        message = "We couldn't find that."
    return error_response(exc.status_code, message)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(422, "Some of the input wasn't valid.")
