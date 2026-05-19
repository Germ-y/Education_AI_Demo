from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain import db_models as rows
from app.domain.models import GenerationJob, GenerationJobStatus

ACTIVE_JOB_STATUSES: set[str] = {"queued", "orchestrating", "content_generating", "asset_generating"}
STALE_JOB_STATUSES: set[str] = {"queued", "orchestrating", "content_generating", "asset_generating"}
_job_create_lock = Lock()


class GenerationJobRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def create_or_get_active(
        self,
        *,
        teacher_id: str,
        student_id: str,
        case_id: str,
        content_type: str,
        requested_goal: str | None,
    ) -> tuple[GenerationJob, bool]:
        with _job_create_lock:
            active_job = self.find_active_for_case(student_id=student_id, case_id=case_id)
            if active_job is not None:
                return active_job, False

            now = _now()
            row = rows.GenerationJobRow(
                id=f"generation_job_{uuid4().hex}",
                teacher_id=teacher_id,
                student_id=student_id,
                case_id=case_id,
                content_type=content_type,
                requested_goal=requested_goal,
                status="queued",
                phase="queued",
                message="생성 작업을 준비 중입니다.",
                orchestrator_run_id=None,
                content_run_id=None,
                content_id=None,
                asset_job_id=None,
                progress_json={"step": "queued"},
                error_code=None,
                error_message=None,
                created_at=now,
                updated_at=now,
                completed_at=None,
            )
            with self.session_factory() as session:
                session.add(row)
                session.commit()
                session.refresh(row)
                return _generation_job(row), True

    def get(self, job_id: str) -> GenerationJob | None:
        with self.session_factory() as session:
            row = session.get(rows.GenerationJobRow, job_id)
            return _generation_job(row) if row else None

    def find_active_for_case(self, *, student_id: str, case_id: str) -> GenerationJob | None:
        with self.session_factory() as session:
            row = session.scalars(
                select(rows.GenerationJobRow)
                .where(
                    rows.GenerationJobRow.student_id == student_id,
                    rows.GenerationJobRow.case_id == case_id,
                    rows.GenerationJobRow.status.in_(ACTIVE_JOB_STATUSES),
                )
                .order_by(rows.GenerationJobRow.updated_at.desc(), rows.GenerationJobRow.created_at.desc())
                .limit(1)
            ).first()
            return _generation_job(row) if row else None

    def list_recent(
        self,
        *,
        student_id: str | None = None,
        case_id: str | None = None,
        statuses: set[str] | None = None,
        limit: int = 50,
    ) -> list[GenerationJob]:
        with self.session_factory() as session:
            statement = select(rows.GenerationJobRow)
            if student_id:
                statement = statement.where(rows.GenerationJobRow.student_id == student_id)
            if case_id:
                statement = statement.where(rows.GenerationJobRow.case_id == case_id)
            if statuses:
                statement = statement.where(rows.GenerationJobRow.status.in_(statuses))
            result = session.scalars(statement.order_by(rows.GenerationJobRow.updated_at.desc()).limit(limit))
            return [_generation_job(row) for row in result]

    def mark_phase(
        self,
        job_id: str,
        *,
        status: GenerationJobStatus,
        message: str,
        progress: dict[str, Any] | None = None,
        orchestrator_run_id: str | None = None,
        content_run_id: str | None = None,
        content_id: str | None = None,
        asset_job_id: str | None = None,
    ) -> GenerationJob | None:
        with self.session_factory() as session:
            row = session.get(rows.GenerationJobRow, job_id)
            if row is None:
                return None
            row.status = status
            row.phase = status
            row.message = message
            if progress is not None:
                row.progress_json = progress
            if orchestrator_run_id is not None:
                row.orchestrator_run_id = orchestrator_run_id
            if content_run_id is not None:
                row.content_run_id = content_run_id
            if content_id is not None:
                row.content_id = content_id
            if asset_job_id is not None:
                row.asset_job_id = asset_job_id
            row.updated_at = _now()
            session.commit()
            session.refresh(row)
            return _generation_job(row)

    def mark_ready(self, job_id: str, *, content_id: str, asset_job_id: str | None, progress: dict[str, Any] | None = None) -> GenerationJob | None:
        with self.session_factory() as session:
            row = session.get(rows.GenerationJobRow, job_id)
            if row is None:
                return None
            now = _now()
            row.status = "ready_for_review"
            row.phase = "ready_for_review"
            row.message = "이미지와 음성까지 준비된 검토 자료가 만들어졌습니다."
            row.content_id = content_id
            row.asset_job_id = asset_job_id
            row.progress_json = progress or {"step": "ready_for_review"}
            row.error_code = None
            row.error_message = None
            row.updated_at = now
            row.completed_at = now
            session.commit()
            session.refresh(row)
            return _generation_job(row)

    def mark_failed(
        self,
        job_id: str,
        *,
        error_code: str,
        error_message: str,
        message: str | None = None,
        content_id: str | None = None,
        asset_job_id: str | None = None,
        progress: dict[str, Any] | None = None,
    ) -> GenerationJob | None:
        with self.session_factory() as session:
            row = session.get(rows.GenerationJobRow, job_id)
            if row is None:
                return None
            now = _now()
            row.status = "failed"
            row.phase = "failed"
            row.message = message or "자료 생성이 중단되었습니다. 다시 시도해 주세요."
            row.error_code = error_code
            row.error_message = error_message
            if content_id is not None:
                row.content_id = content_id
            if asset_job_id is not None:
                row.asset_job_id = asset_job_id
            if progress is not None:
                row.progress_json = progress
            row.updated_at = now
            row.completed_at = now
            session.commit()
            session.refresh(row)
            return _generation_job(row)

    def mark_stale_running_failed(self, *, max_age_seconds: int) -> list[GenerationJob]:
        cutoff = datetime.now(UTC) - timedelta(seconds=max_age_seconds)
        force_stale = max_age_seconds <= 0
        stale_jobs: list[GenerationJob] = []
        with self.session_factory() as session:
            result = session.scalars(
                select(rows.GenerationJobRow)
                .where(rows.GenerationJobRow.status.in_(STALE_JOB_STATUSES))
                .order_by(rows.GenerationJobRow.updated_at.asc())
                .limit(200)
            )
            for row in result:
                updated_at = _parse_timestamp(row.updated_at or row.created_at)
                if not force_stale and (updated_at is None or updated_at >= cutoff):
                    continue
                now = _now()
                row.status = "failed"
                row.phase = "failed"
                row.message = "생성 작업이 제한 시간 안에 완료되지 않아 다시 생성이 필요합니다."
                row.error_code = "GENERATION_JOB_STALE_RUNNING"
                row.error_message = "서버 재시작 또는 provider 지연으로 생성 작업이 오래 running 상태에 머물렀습니다."
                row.updated_at = now
                row.completed_at = now
                stale_jobs.append(_generation_job(row))
            if stale_jobs:
                session.commit()
        return stale_jobs


def _generation_job(row: rows.GenerationJobRow) -> GenerationJob:
    return GenerationJob.model_validate(
        {
            "id": row.id,
            "teacherId": row.teacher_id,
            "studentId": row.student_id,
            "caseId": row.case_id,
            "contentType": row.content_type,
            "requestedGoal": row.requested_goal,
            "status": row.status,
            "phase": row.phase,
            "message": row.message,
            "orchestratorRunId": row.orchestrator_run_id,
            "contentRunId": row.content_run_id,
            "contentId": row.content_id,
            "assetJobId": row.asset_job_id,
            "progressJson": row.progress_json or {},
            "errorCode": row.error_code,
            "errorMessage": row.error_message,
            "createdAt": row.created_at,
            "updatedAt": row.updated_at,
            "completedAt": row.completed_at,
        }
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
