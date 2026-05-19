from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.response import ok
from app.api.routes import ai, audit, auth, contents, context, public_data, review, student, teacher
from app.core.config import get_settings
from app.core.logging import configure_generation_logging
from app.db.session import create_schema, get_session_maker
from app.repositories.demo_repository import DemoRepository
from app.repositories.generation_job_repository import GenerationJobRepository
from app.services.store import DemoStore


def cleanup_stale_generation_jobs() -> None:
    create_schema()
    session_maker = get_session_maker()
    GenerationJobRepository(session_maker).mark_stale_running_failed(max_age_seconds=45 * 60)
    DemoStore(repository=DemoRepository(session_maker)).mark_stale_generating_mission_contents_failed(max_age_seconds=45 * 60)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    cleanup_stale_generation_jobs()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_generation_logging(settings)
    app = FastAPI(title="EduYJ Backend", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(context.router)
    app.include_router(ai.router)
    app.include_router(audit.router)
    app.include_router(contents.router)
    app.include_router(review.router)
    app.include_router(review.teacher_reports_router)
    app.include_router(teacher.router)
    app.include_router(student.router)
    app.include_router(public_data.router)
    app.mount("/generated", StaticFiles(directory=settings.generated_assets_dir, check_dir=False), name="generated")

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

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict):
            code = str(detail.get("code", "HTTP_ERROR"))
            message = str(detail.get("message", "요청을 처리할 수 없습니다."))
            details = detail.get("details", {})
        else:
            code = "HTTP_ERROR"
            message = str(detail)
            details = {}

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "details": details,
                }
            },
            headers=exc.headers,
        )

    return app


app = create_app()
