from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.response import ok
from app.api.routes import auth, public_data, student, teacher
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    app = FastAPI(title="EduYJ Backend", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(teacher.router)
    app.include_router(student.router)
    app.include_router(public_data.router)

    @app.get("/health")
    def health() -> dict:
        return ok({"status": "ok", "service": "eduyj-backend", "mode": "demo-seed", "framework": "fastapi"})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "요청 형식이 올바르지 않습니다.",
                    "details": exc.errors(),
                }
            },
        )

    return app


app = create_app()
