from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain import db_models as rows
from app.domain.models import AgentRun


class AgentRunRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def create_running(
        self,
        *,
        agent_type: str,
        prompt_version: str,
        output_schema_name: str,
        input_snapshot: dict[str, Any],
        model: str,
    ) -> AgentRun:
        row = rows.AgentRunRow(
            id=f"agent_run_{uuid4()}",
            agent_type=agent_type,
            prompt_version=prompt_version,
            output_schema_name=output_schema_name,
            input_snapshot_json=input_snapshot,
            output_json=None,
            model=model,
            status="running",
            token_usage_json=None,
            error_code=None,
            error_message=None,
            review_required=False,
            created_at=_now(),
            completed_at=None,
        )
        with self.session_factory() as session:
            session.add(row)
            session.commit()
            session.refresh(row)
            return _agent_run(row)

    def find_running_generation_for_case(
        self,
        *,
        student_id: str,
        case_id: str,
        agent_type: str,
        max_age_seconds: int = 60 * 60,
    ) -> AgentRun | None:
        cutoff = datetime.now(UTC) - timedelta(seconds=max_age_seconds)
        with self.session_factory() as session:
            result = session.scalars(
                select(rows.AgentRunRow)
                .where(rows.AgentRunRow.agent_type == agent_type, rows.AgentRunRow.status == "running")
                .order_by(rows.AgentRunRow.created_at.desc())
                .limit(100)
            )
            for row in result:
                snapshot = row.input_snapshot_json or {}
                if snapshot.get("studentId") != student_id or snapshot.get("caseId") != case_id:
                    continue
                created_at = _parse_timestamp(row.created_at)
                if created_at is not None and created_at < cutoff:
                    continue
                return _agent_run(row)
        return None

    def find_content_generation_for_orchestrator(self, orchestrator_run_id: str) -> AgentRun | None:
        with self.session_factory() as session:
            result = session.scalars(
                select(rows.AgentRunRow)
                .where(rows.AgentRunRow.agent_type == "content", rows.AgentRunRow.status.in_(["running", "succeeded"]))
                .order_by(rows.AgentRunRow.created_at.desc())
                .limit(100)
            )
            for row in result:
                snapshot = row.input_snapshot_json or {}
                if snapshot.get("orchestratorRunId") == orchestrator_run_id:
                    return _agent_run(row)
        return None

    def mark_succeeded(self, agent_run_id: str, *, output_json: dict[str, Any], token_usage: dict[str, Any] | None) -> AgentRun | None:
        with self.session_factory() as session:
            row = session.get(rows.AgentRunRow, agent_run_id)
            if row is None:
                return None
            row.status = "succeeded"
            row.output_json = output_json
            row.token_usage_json = token_usage
            row.error_code = None
            row.error_message = None
            row.review_required = False
            row.completed_at = _now()
            session.commit()
            session.refresh(row)
            return _agent_run(row)

    def mark_failed(self, agent_run_id: str, *, error_code: str, error_message: str, review_required: bool = True) -> AgentRun | None:
        with self.session_factory() as session:
            row = session.get(rows.AgentRunRow, agent_run_id)
            if row is None:
                return None
            row.status = "failed"
            row.output_json = None
            row.error_code = error_code
            row.error_message = error_message
            row.review_required = review_required
            row.completed_at = _now()
            session.commit()
            session.refresh(row)
            return _agent_run(row)

    def get(self, agent_run_id: str) -> AgentRun | None:
        with self.session_factory() as session:
            row = session.get(rows.AgentRunRow, agent_run_id)
            return _agent_run(row) if row else None

    def list_recent(self, *, limit: int = 20) -> list[AgentRun]:
        with self.session_factory() as session:
            result = session.scalars(select(rows.AgentRunRow).order_by(rows.AgentRunRow.created_at.desc()).limit(limit))
            return [_agent_run(row) for row in result]


def _agent_run(row: rows.AgentRunRow) -> AgentRun:
    return AgentRun.model_validate(
        {
            "id": row.id,
            "agentType": row.agent_type,
            "promptVersion": row.prompt_version,
            "outputSchemaName": row.output_schema_name,
            "inputSnapshotJson": row.input_snapshot_json,
            "outputJson": row.output_json,
            "model": row.model,
            "status": row.status,
            "tokenUsageJson": row.token_usage_json,
            "errorCode": row.error_code,
            "errorMessage": row.error_message,
            "reviewRequired": row.review_required,
            "createdAt": row.created_at,
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
