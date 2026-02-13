from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: list[dict] | None = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


def _payload(code: str, message: str, details: list[dict] | None = None) -> dict:
    return {"code": code, "message": message, "details": details or []}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(item) for item in err["loc"] if item != "body"),
                "message": err["msg"],
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=400,
            content=_payload("VALIDATION_ERROR", "Request validation failed", details),
        )
