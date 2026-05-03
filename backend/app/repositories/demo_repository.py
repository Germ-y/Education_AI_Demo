from collections.abc import Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.domain import db_models as rows
from app.domain.models import DemoDatabase
from app.domain.schemas import MissionContent


class DemoRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def is_empty(self) -> bool:
        with self.session_factory() as session:
            return session.scalar(select(rows.OrganizationRow.id).limit(1)) is None

    def replace_database(self, db: DemoDatabase, *, preserve_agent_runs: bool = False) -> None:
        with self.session_factory() as session:
            _delete_all(session, preserve_agent_runs=preserve_agent_runs)
            _insert_all(session, db)
            session.commit()

    def load_database(self) -> DemoDatabase:
        with self.session_factory() as session:
            stages_by_content = _group_by_content(
                session.scalars(select(rows.ContentStageRow).order_by(rows.ContentStageRow.sort_order)).all()
            )
            assets_by_content = _group_by_content(session.scalars(select(rows.ContentAssetRow).order_by(rows.ContentAssetRow.id)).all())

            mission_contents = [
                _mission_from_row(content, stages_by_content.get(content.id, []), assets_by_content.get(content.id, []))
                for content in session.scalars(select(rows.MissionContentRow).order_by(rows.MissionContentRow.id)).all()
            ]

            return DemoDatabase.model_validate(
                {
                    "organizations": [_organization(row) for row in session.scalars(select(rows.OrganizationRow).order_by(rows.OrganizationRow.id))],
                    "users": [_user(row) for row in session.scalars(select(rows.UserRow).order_by(rows.UserRow.id))],
                    "students": [_student(row) for row in session.scalars(select(rows.StudentRow).order_by(rows.StudentRow.id))],
                    "studentAccounts": [_student_account(row) for row in session.scalars(select(rows.StudentAccountRow).order_by(rows.StudentAccountRow.id))],
                    "schools": [_school(row) for row in session.scalars(select(rows.SchoolProfileRow).order_by(rows.SchoolProfileRow.school_name))],
                    "schoolCalendarEvents": [
                        _school_calendar_event(row)
                        for row in session.scalars(select(rows.SchoolCalendarEventRow).order_by(rows.SchoolCalendarEventRow.event_date))
                    ],
                    "schoolTimetableSlots": [
                        _school_timetable_slot(row)
                        for row in session.scalars(
                            select(rows.SchoolTimetableSlotRow).order_by(
                                rows.SchoolTimetableSlotRow.timetable_date,
                                rows.SchoolTimetableSlotRow.grade,
                                rows.SchoolTimetableSlotRow.class_name,
                                rows.SchoolTimetableSlotRow.period,
                            )
                        )
                    ],
                    "supportCases": [_support_case(row) for row in session.scalars(select(rows.SupportCaseRow).order_by(rows.SupportCaseRow.id))],
                    "caseNotes": [_case_note(row) for row in session.scalars(select(rows.CaseNoteRow).order_by(rows.CaseNoteRow.created_at))],
                    "memoryCards": [_memory_card(row) for row in session.scalars(select(rows.MemoryCardRow).order_by(rows.MemoryCardRow.id))],
                    "plannerItems": [_planner_item(row) for row in session.scalars(select(rows.PlannerItemRow).order_by(rows.PlannerItemRow.id))],
                    "missionContents": mission_contents,
                    "attempts": [_attempt(row) for row in session.scalars(select(rows.ContentAttemptRow).order_by(rows.ContentAttemptRow.started_at))],
                    "activityEvents": [
                        _activity_event(row) for row in session.scalars(select(rows.ActivityEventRow).order_by(rows.ActivityEventRow.occurred_at))
                    ],
                    "realtimeSessions": [
                        _realtime_session(row) for row in session.scalars(select(rows.RealtimePracticeSessionRow).order_by(rows.RealtimePracticeSessionRow.id))
                    ],
                    "reviewSummaries": [
                        _review_summary(row) for row in session.scalars(select(rows.ReviewSummaryRow).order_by(rows.ReviewSummaryRow.id))
                    ],
                    "auditLogs": [_audit_log(row) for row in session.scalars(select(rows.AuditLogRow).order_by(rows.AuditLogRow.created_at))],
                    "publicDataSources": [
                        _public_data_source(row) for row in session.scalars(select(rows.PublicDataSourceRow).order_by(rows.PublicDataSourceRow.id))
                    ],
                }
            )


def _delete_all(session: Session, *, preserve_agent_runs: bool = False) -> None:
    models = [
        rows.AuditLogRow,
        rows.ReviewSummaryRow,
        rows.RealtimePracticeSessionRow,
        rows.ActivityEventRow,
        rows.ContentAttemptRow,
        rows.ContentAssetRow,
        rows.ContentStageRow,
        rows.MissionContentRow,
        rows.PlannerItemRow,
        rows.MemoryCardRow,
        rows.CaseNoteRow,
        rows.SupportCaseRow,
        rows.SchoolTimetableSlotRow,
        rows.SchoolCalendarEventRow,
        rows.SchoolProfileRow,
        rows.StudentAccountRow,
        rows.StudentRow,
        rows.UserRow,
        rows.OrganizationRow,
        rows.PublicDataSourceRow,
    ]
    if not preserve_agent_runs:
        models.insert(0, rows.AgentRunRow)
    for model in models:
        session.execute(delete(model))


def _insert_all(session: Session, db: DemoDatabase) -> None:
    session.add_all(
        rows.OrganizationRow(
            id=item.id,
            external_key=item.external_key,
            name=item.name,
            type=item.type,
            region_code=item.region_code,
        )
        for item in db.organizations
    )
    session.add_all(
        rows.UserRow(
            id=item.id,
            organization_id=item.organization_id,
            email=item.email,
            display_name=item.display_name,
            role=item.role,
            password_hash=None,
            status=item.status,
        )
        for item in db.users
    )
    session.add_all(
        rows.StudentRow(
            id=item.id,
            organization_id=item.organization_id,
            external_key=item.external_key,
            display_name=item.display_name,
            grade=item.grade,
            school_code=item.school_code,
            student_type=item.student_type,
            primary_need=item.primary_need,
            profile_json=item.profile_json,
            status=item.status,
        )
        for item in db.students
    )
    session.add_all(
        rows.StudentAccountRow(id=item.id, student_id=item.student_id, access_code=item.access_code, status=item.status)
        for item in db.student_accounts
    )
    session.add_all(
        rows.SchoolProfileRow(
            id=item.id,
            office_code=item.office_code,
            school_code=item.school_code,
            school_name=item.school_name,
            school_kind=item.school_kind,
            region_name=item.region_name,
            road_address=item.road_address,
            source_code=item.source_code,
        )
        for item in db.schools
    )
    session.add_all(
        rows.SchoolCalendarEventRow(
            id=item.id,
            school_code=item.school_code,
            office_code=item.office_code,
            academic_year=item.academic_year,
            event_date=item.event_date,
            event_name=item.event_name,
            event_content=item.event_content,
            schedule_type=item.schedule_type,
            applies_to_grades=item.applies_to_grades,
            source_code=item.source_code,
            retrieved_at=item.retrieved_at,
        )
        for item in db.school_calendar_events
    )
    session.add_all(
        rows.SchoolTimetableSlotRow(
            id=item.id,
            school_code=item.school_code,
            office_code=item.office_code,
            academic_year=item.academic_year,
            semester=item.semester,
            timetable_date=item.timetable_date,
            grade=item.grade,
            class_name=item.class_name,
            period=item.period,
            subject_name=item.subject_name,
            source_code=item.source_code,
            retrieved_at=item.retrieved_at,
        )
        for item in db.school_timetable_slots
    )
    session.add_all(
        rows.SupportCaseRow(
            id=item.id,
            student_id=item.student_id,
            owner_teacher_id=item.owner_teacher_id,
            case_status=item.case_status,
            current_goal=item.current_goal,
            dashboard_stage=item.dashboard_stage,
            support_strategy=item.support_strategy,
            opened_at=item.opened_at,
        )
        for item in db.support_cases
    )
    session.add_all(
        rows.CaseNoteRow(
            id=item.id,
            case_id=item.case_id,
            author_id=item.author_id,
            note_type=item.note_type,
            body=item.body,
            visibility=item.visibility,
            created_at=item.created_at,
        )
        for item in db.case_notes
    )
    session.add_all(
        rows.MemoryCardRow(
            id=item.id,
            student_id=item.student_id,
            case_id=item.case_id,
            version=item.version,
            learning_problem_types=item.learning_problem_types,
            recent_4w_response_json=item.recent_4w_response_json,
            emotional_state_note=item.emotional_state_note,
            effective_explanation_styles=item.effective_explanation_styles,
            frequent_blocking_units=item.frequent_blocking_units,
            guardian_cooperation_status=item.guardian_cooperation_status,
            next_session_cautions=item.next_session_cautions,
            teacher_verified_at=item.teacher_verified_at,
            status=item.status,
        )
        for item in db.memory_cards
    )
    session.add_all(
        rows.PlannerItemRow(
            id=item.id,
            student_id=item.student_id,
            case_id=item.case_id,
            period_type=item.period_type,
            goal_text=item.goal_text,
            checklist_json=item.checklist_json,
            status=item.status,
        )
        for item in db.planner_items
    )
    for content in db.mission_contents:
        session.add(
            rows.MissionContentRow(
                id=content.id,
                case_id=content.case_id,
                student_id=content.student_id,
                content_type=content.content_type,
                title=content.title,
                session_goal=content.session_goal,
                status=content.status,
                total_steps=content.total_steps,
                brief_json=content.brief_json,
                teacher_review_summary=content.teacher_review_summary,
                approved_by_user_id=content.approved_by_user_id,
                approved_at=content.approved_at,
                published_at=content.published_at,
            )
        )
        session.add_all(
            rows.ContentStageRow(
                id=stage.id,
                mission_content_id=stage.mission_content_id,
                step=stage.step,
                stage_role=stage.stage_role,
                template_type=stage.template_type,
                student_title=stage.student_title,
                student_instruction=stage.student_instruction,
                template_json=stage.template_json,
                realtime_spec_json=stage.realtime_spec.model_dump(by_alias=True) if stage.realtime_spec else None,
                sort_order=stage.sort_order,
            )
            for stage in content.stages
        )
        session.add_all(
            rows.ContentAssetRow(
                id=asset.id,
                mission_content_id=asset.mission_content_id,
                stage_id=asset.stage_id,
                asset_role=asset.asset_role,
                asset_type=asset.asset_type,
                provider=asset.provider,
                model=asset.model,
                prompt_json=asset.prompt_json,
                source_text=asset.source_text,
                storage_url=asset.storage_url,
                preview_url=asset.preview_url,
                qa_status=asset.qa_status,
                approval_status=asset.approval_status,
            )
            for asset in content.assets
        )
    session.add_all(
        rows.ContentAttemptRow(
            id=item.id,
            mission_content_id=item.mission_content_id,
            student_id=item.student_id,
            status=item.status,
            current_step=item.current_step,
            started_at=item.started_at,
            completed_at=item.completed_at,
            score_json=item.score_json,
        )
        for item in db.attempts
    )
    session.add_all(
        rows.ActivityEventRow(
            id=item.id,
            attempt_id=item.attempt_id,
            student_id=item.student_id,
            stage_id=item.stage_id,
            event_type=item.event_type,
            payload_json=item.payload_json,
            occurred_at=item.occurred_at,
        )
        for item in db.activity_events
    )
    session.add_all(
        rows.RealtimePracticeSessionRow(
            id=item.id,
            attempt_id=item.attempt_id,
            mission_content_id=item.mission_content_id,
            stage_id=item.stage_id,
            student_id=item.student_id,
            provider=item.provider,
            model=item.model,
            status=item.status,
            spec_snapshot_json=item.spec_snapshot_json,
            started_at=item.started_at,
            ended_at=item.ended_at,
            turn_count=item.turn_count,
            duration_sec=item.duration_sec,
            rubric_result_json=item.rubric_result_json,
            transcript_summary=item.transcript_summary,
        )
        for item in db.realtime_sessions
    )
    session.add_all(
        rows.ReviewSummaryRow(
            id=item.id,
            attempt_id=item.attempt_id,
            student_id=item.student_id,
            completion_rate=item.completion_rate,
            accuracy_rate=item.accuracy_rate,
            short_summary=item.short_summary,
            wrong_pattern_json=item.wrong_pattern_json,
            realtime_result_json=item.realtime_result_json,
        )
        for item in db.review_summaries
    )
    session.add_all(
        rows.PublicDataSourceRow(
            id=item.id,
            source_code=item.source_code,
            name=item.name,
            base_url=item.base_url,
            auth_type=item.auth_type,
            enabled=item.enabled,
        )
        for item in db.public_data_sources
    )
    session.add_all(
        rows.AuditLogRow(
            id=item.id,
            actor_user_id=item.actor_user_id,
            student_id=item.student_id,
            action=item.action,
            resource_type=item.resource_type,
            resource_id=item.resource_id,
            payload_json=item.payload_json,
            created_at=item.created_at,
        )
        for item in db.audit_logs
    )


def _group_by_content(items: Iterable) -> dict[str, list]:
    grouped: dict[str, list] = {}
    for item in items:
        grouped.setdefault(item.mission_content_id, []).append(item)
    return grouped


def _organization(row: rows.OrganizationRow) -> dict:
    return {"id": row.id, "externalKey": row.external_key, "name": row.name, "type": row.type, "regionCode": row.region_code}


def _user(row: rows.UserRow) -> dict:
    return {
        "id": row.id,
        "organizationId": row.organization_id,
        "email": row.email,
        "displayName": row.display_name,
        "role": row.role,
        "status": row.status,
    }


def _student(row: rows.StudentRow) -> dict:
    return {
        "id": row.id,
        "organizationId": row.organization_id,
        "externalKey": row.external_key,
        "displayName": row.display_name,
        "grade": row.grade,
        "schoolCode": row.school_code,
        "studentType": row.student_type,
        "primaryNeed": row.primary_need,
        "profileJson": row.profile_json,
        "status": row.status,
    }


def _student_account(row: rows.StudentAccountRow) -> dict:
    return {"id": row.id, "studentId": row.student_id, "accessCode": row.access_code, "status": row.status}


def _school(row: rows.SchoolProfileRow) -> dict:
    return {
        "id": row.id,
        "officeCode": row.office_code,
        "schoolCode": row.school_code,
        "schoolName": row.school_name,
        "schoolKind": row.school_kind,
        "regionName": row.region_name,
        "roadAddress": row.road_address,
        "sourceCode": row.source_code,
    }


def _school_calendar_event(row: rows.SchoolCalendarEventRow) -> dict:
    return {
        "id": row.id,
        "schoolCode": row.school_code,
        "officeCode": row.office_code,
        "academicYear": row.academic_year,
        "eventDate": row.event_date,
        "eventName": row.event_name,
        "eventContent": row.event_content,
        "scheduleType": row.schedule_type,
        "appliesToGrades": row.applies_to_grades,
        "sourceCode": row.source_code,
        "retrievedAt": row.retrieved_at,
    }


def _school_timetable_slot(row: rows.SchoolTimetableSlotRow) -> dict:
    return {
        "id": row.id,
        "schoolCode": row.school_code,
        "officeCode": row.office_code,
        "academicYear": row.academic_year,
        "semester": row.semester,
        "timetableDate": row.timetable_date,
        "grade": row.grade,
        "className": row.class_name,
        "period": row.period,
        "subjectName": row.subject_name,
        "sourceCode": row.source_code,
        "retrievedAt": row.retrieved_at,
    }


def _support_case(row: rows.SupportCaseRow) -> dict:
    return {
        "id": row.id,
        "studentId": row.student_id,
        "ownerTeacherId": row.owner_teacher_id,
        "caseStatus": row.case_status,
        "currentGoal": row.current_goal,
        "dashboardStage": row.dashboard_stage,
        "supportStrategy": row.support_strategy,
        "openedAt": row.opened_at,
    }


def _case_note(row: rows.CaseNoteRow) -> dict:
    return {
        "id": row.id,
        "caseId": row.case_id,
        "authorId": row.author_id,
        "noteType": row.note_type,
        "body": row.body,
        "visibility": row.visibility,
        "createdAt": row.created_at,
    }


def _memory_card(row: rows.MemoryCardRow) -> dict:
    return {
        "id": row.id,
        "studentId": row.student_id,
        "caseId": row.case_id,
        "version": row.version,
        "learningProblemTypes": row.learning_problem_types,
        "recent4wResponseJson": row.recent_4w_response_json,
        "emotionalStateNote": row.emotional_state_note,
        "effectiveExplanationStyles": row.effective_explanation_styles,
        "frequentBlockingUnits": row.frequent_blocking_units,
        "guardianCooperationStatus": row.guardian_cooperation_status,
        "nextSessionCautions": row.next_session_cautions,
        "teacherVerifiedAt": row.teacher_verified_at,
        "status": row.status,
    }


def _planner_item(row: rows.PlannerItemRow) -> dict:
    return {
        "id": row.id,
        "studentId": row.student_id,
        "caseId": row.case_id,
        "periodType": row.period_type,
        "goalText": row.goal_text,
        "checklistJson": row.checklist_json,
        "status": row.status,
    }


def _mission_from_row(content: rows.MissionContentRow, stages: list[rows.ContentStageRow], assets: list[rows.ContentAssetRow]) -> MissionContent:
    return MissionContent.model_validate(
        {
            "id": content.id,
            "caseId": content.case_id,
            "studentId": content.student_id,
            "contentType": content.content_type,
            "title": content.title,
            "sessionGoal": content.session_goal,
            "status": content.status,
            "totalSteps": content.total_steps,
            "briefJson": content.brief_json,
            "teacherReviewSummary": content.teacher_review_summary,
            "approvedByUserId": content.approved_by_user_id,
            "approvedAt": content.approved_at,
            "publishedAt": content.published_at,
            "stages": [_stage(row) for row in stages],
            "assets": [_asset(row) for row in assets],
        }
    )


def _stage(row: rows.ContentStageRow) -> dict:
    template_json = _normalize_template_json(row.template_type, row.template_json)
    return {
        "id": row.id,
        "missionContentId": row.mission_content_id,
        "step": row.step,
        "stageRole": row.stage_role,
        "templateType": row.template_type,
        "studentTitle": row.student_title,
        "studentInstruction": row.student_instruction,
        "templateJson": template_json,
        "realtimeSpec": row.realtime_spec_json,
        "sortOrder": row.sort_order,
    }


def _normalize_template_json(template_type: str, template_json: dict | None) -> dict | None:
    if template_type != "blank_fill" or not isinstance(template_json, dict):
        return template_json

    sentence = str(template_json.get("sentence") or template_json.get("question") or "")
    if "__" in sentence or "[A]" in sentence or "[B]" in sentence:
        return template_json

    return {**template_json, "sentence": _legacy_blank_fill_sentence(template_json)}


def _legacy_blank_fill_sentence(template_json: dict) -> str:
    values = _legacy_blank_values(template_json)
    question = str(template_json.get("question") or "")
    if len(values) >= 2:
        return "분수는 __ / __입니다."
    if "시계" in question or "정각" in question:
        return "시계는 __시예요."
    return "알맞은 말은 __입니다."


def _legacy_blank_values(template_json: dict) -> list[str]:
    accepted_answers = template_json.get("acceptedAnswers") or template_json.get("answers")
    if isinstance(accepted_answers, list) and accepted_answers and isinstance(accepted_answers[0], dict):
        return [str(value) for value in accepted_answers[0].values()]
    tiles = template_json.get("tiles")
    if isinstance(tiles, list):
        return [str(value) for value in tiles]
    return []


def _asset(row: rows.ContentAssetRow) -> dict:
    return {
        "id": row.id,
        "missionContentId": row.mission_content_id,
        "stageId": row.stage_id,
        "assetRole": row.asset_role,
        "assetType": row.asset_type,
        "provider": row.provider,
        "model": row.model,
        "promptJson": row.prompt_json,
        "sourceText": row.source_text,
        "storageUrl": row.storage_url,
        "previewUrl": row.preview_url,
        "qaStatus": row.qa_status,
        "approvalStatus": row.approval_status,
    }


def _attempt(row: rows.ContentAttemptRow) -> dict:
    return {
        "id": row.id,
        "missionContentId": row.mission_content_id,
        "studentId": row.student_id,
        "status": row.status,
        "currentStep": row.current_step,
        "startedAt": row.started_at,
        "completedAt": row.completed_at,
        "scoreJson": row.score_json,
    }


def _activity_event(row: rows.ActivityEventRow) -> dict:
    return {
        "id": row.id,
        "attemptId": row.attempt_id,
        "studentId": row.student_id,
        "stageId": row.stage_id,
        "eventType": row.event_type,
        "payloadJson": row.payload_json,
        "occurredAt": row.occurred_at,
    }


def _realtime_session(row: rows.RealtimePracticeSessionRow) -> dict:
    return {
        "id": row.id,
        "attemptId": row.attempt_id,
        "missionContentId": row.mission_content_id,
        "stageId": row.stage_id,
        "studentId": row.student_id,
        "provider": row.provider,
        "model": row.model,
        "status": row.status,
        "specSnapshotJson": row.spec_snapshot_json,
        "startedAt": row.started_at,
        "endedAt": row.ended_at,
        "turnCount": row.turn_count,
        "durationSec": row.duration_sec,
        "rubricResultJson": row.rubric_result_json,
        "transcriptSummary": row.transcript_summary,
    }


def _public_data_source(row: rows.PublicDataSourceRow) -> dict:
    return {
        "id": row.id,
        "sourceCode": row.source_code,
        "name": row.name,
        "baseUrl": row.base_url,
        "authType": row.auth_type,
        "enabled": row.enabled,
    }


def _review_summary(row: rows.ReviewSummaryRow) -> dict:
    return {
        "id": row.id,
        "attemptId": row.attempt_id,
        "studentId": row.student_id,
        "completionRate": float(row.completion_rate),
        "accuracyRate": float(row.accuracy_rate),
        "shortSummary": row.short_summary,
        "wrongPatternJson": row.wrong_pattern_json,
        "realtimeResultJson": row.realtime_result_json,
    }


def _audit_log(row: rows.AuditLogRow) -> dict:
    return {
        "id": row.id,
        "actorUserId": row.actor_user_id,
        "studentId": row.student_id,
        "action": row.action,
        "resourceType": row.resource_type,
        "resourceId": row.resource_id,
        "payloadJson": row.payload_json,
        "createdAt": row.created_at,
    }
