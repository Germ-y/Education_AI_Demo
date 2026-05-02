from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import get_settings
from app.data.demo_data import create_demo_database
from app.domain.enums import MissionStatus
from app.domain.models import (
    ActivityEvent,
    AuditLog,
    CaseNote,
    ContentAttempt,
    DemoDatabase,
    MemoryCard,
    RealtimePracticeSession,
    ReviewSummary,
    SchoolCalendarEvent,
    SchoolProfile,
    SchoolTimetableSlot,
)
from app.domain.schemas import MissionContent
from app.repositories.demo_repository import DemoRepository


class SessionPrincipal(BaseModel):
    token: str
    kind: str
    id: str
    role: str
    student_id: str | None = Field(default=None, alias="studentId")
    expires_at: str = Field(alias="expiresAt")

    model_config = ConfigDict(populate_by_name=True)


class DemoStore:
    def __init__(self, seed: DemoDatabase | None = None, repository: DemoRepository | None = None) -> None:
        self.repository = repository
        self.db = repository.load_database() if repository else seed or create_demo_database()
        self.sessions: dict[str, SessionPrincipal] = {}

    def refresh(self) -> None:
        if self.repository is not None:
            self.db = self.repository.load_database()

    def persist(self) -> None:
        if self.repository is not None:
            self.repository.replace_database(self.db, preserve_agent_runs=True)

    def create_user_session(self, role: str, email: str | None = None) -> SessionPrincipal | None:
        self.refresh()
        user = next((candidate for candidate in self.db.users if candidate.role == role and (email is None or candidate.email == email)), None)
        if user is None:
            return None
        session = self._create_session(kind="user", id=user.id, role=user.role)
        self.sessions[session.token] = session
        return session

    def create_student_session(self, access_code: str) -> SessionPrincipal | None:
        self.refresh()
        account = next(
            (candidate for candidate in self.db.student_accounts if candidate.status == "active" and candidate.access_code == access_code),
            None,
        )
        if account is None:
            return None
        session = self._create_session(kind="student", id=account.id, role="student", student_id=account.student_id)
        self.sessions[session.token] = session
        return session

    def get_session(self, token: str | None) -> SessionPrincipal | None:
        if token is None:
            return None
        return self.sessions.get(token)

    def get_seed_context(self) -> dict:
        self.refresh()
        organization = self.db.organizations[0]
        teacher = next(user for user in self.db.users if user.role == "teacher")
        student_accounts = {account.student_id: account for account in self.db.student_accounts if account.status == "active"}
        return {
            "mode": "demo_seed",
            "organization": organization.model_dump(by_alias=True),
            "teacher": teacher.model_dump(by_alias=True),
            "students": [
                {
                    **student_summary,
                    "accessCode": student_accounts[student_summary["studentId"]].access_code
                    if student_summary["studentId"] in student_accounts
                    else None,
                }
                for student_summary in self.list_teacher_students(teacher_id=teacher.id)
            ],
            "assignments": [
                {
                    "teacherId": support_case.owner_teacher_id,
                    "studentId": support_case.student_id,
                    "caseId": support_case.id,
                    "caseStatus": support_case.case_status,
                    "dashboardStage": support_case.dashboard_stage,
                    "supportStrategy": _teacher_facing_text(support_case.support_strategy),
                }
                for support_case in self.db.support_cases
                if support_case.owner_teacher_id == teacher.id
            ],
            "missionMappings": [
                {
                    "contentId": content.id,
                    "studentId": content.student_id,
                    "caseId": content.case_id,
                    "title": content.title,
                    "status": content.status,
                    "totalSteps": content.total_steps,
                    "updatedAt": _mission_updated_at(content),
                }
                for content in sorted(self.db.mission_contents, key=_mission_mapping_sort_key, reverse=True)
            ],
        }

    def record_audit(
        self,
        *,
        actor_user_id: str | None,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        student_id: str | None = None,
        payload_json: dict[str, Any] | None = None,
    ) -> AuditLog:
        log = AuditLog(
            id=f"audit_{uuid4()}",
            actorUserId=actor_user_id,
            studentId=student_id,
            action=action,
            resourceType=resource_type,
            resourceId=resource_id,
            payloadJson=payload_json or {},
            createdAt=_now(),
        )
        self.db.audit_logs.append(log)
        self.persist()
        return log

    def list_audit_logs(self, *, student_id: str | None = None, action: str | None = None, limit: int = 50) -> list[dict]:
        self.refresh()
        logs = self.db.audit_logs
        if student_id:
            logs = [log for log in logs if log.student_id == student_id]
        if action:
            logs = [log for log in logs if log.action == action]
        return [log.model_dump(by_alias=True) for log in logs[-limit:]]

    def list_teacher_students(self, student_type: str | None = None, q: str | None = None, teacher_id: str | None = None) -> list[dict]:
        self.refresh()
        open_cases = [
            support_case
            for support_case in self.db.support_cases
            if support_case.case_status == "open" and (teacher_id is None or support_case.owner_teacher_id == teacher_id)
        ]
        open_case_by_student_id = {support_case.student_id: support_case for support_case in open_cases}

        students = []
        for student in self.db.students:
            if student.id not in open_case_by_student_id:
                continue
            if student_type and student.student_type != student_type:
                continue
            if q and q not in student.display_name and q not in student.primary_need:
                continue
            school = self.get_school(student.school_code)
            latest_content = next(
                iter(
                    sorted(
                        [content for content in self.db.mission_contents if content.student_id == student.id],
                        key=_mission_mapping_sort_key,
                        reverse=True,
                    )
                ),
                None,
            )
            planner = next(
                (
                    item
                    for item in self.db.planner_items
                    if item.student_id == student.id and item.period_type == "next_session" and item.status == "planned"
                ),
                None,
            )
            dashboard = _student_dashboard(student.profile_json)
            stage_label = _dashboard_stage_label(open_case_by_student_id[student.id].dashboard_stage)
            students.append(
                {
                    "studentId": student.id,
                    "displayName": student.display_name,
                    "grade": student.grade,
                    "gradeLabel": dashboard.get("gradeLabel") or _grade_label(student.grade),
                    "schoolCode": student.school_code,
                    "schoolName": school.school_name if school else None,
                    "studentType": student.student_type,
                    "studentTypeLabel": dashboard.get("studentTypeLabel") or _student_type_label(student.student_type),
                    "trackLabel": dashboard.get("trackLabel") or _student_type_label(student.student_type),
                    "primaryNeed": student.primary_need,
                    "attendanceRate": dashboard.get("attendanceRate"),
                    "attendanceLabel": dashboard.get("attendanceLabel") or _attendance_label(dashboard.get("attendanceRate")),
                    "strengths": _student_dashboard_list(student.profile_json, "strengths"),
                    "weaknesses": _student_dashboard_list(student.profile_json, "weaknesses"),
                    "latestContentStatus": latest_content.status if latest_content else "none",
                    "dashboardStage": open_case_by_student_id[student.id].dashboard_stage,
                    "dashboardStageLabel": stage_label,
                    "statusLabel": dashboard.get("statusLabel") or stage_label,
                    "supportStrategy": _teacher_facing_text(open_case_by_student_id[student.id].support_strategy),
                    "summaryLine": _teacher_facing_text(dashboard.get("summaryLine") or student.primary_need),
                    "aiContextSummary": _teacher_facing_text(dashboard.get("aiContextSummary") or student.primary_need),
                    "nextSessionSuggestion": _teacher_facing_text(planner.goal_text if planner else "다음 회기 목표를 설정해 주세요."),
                }
            )
        return students

    def get_student_case_file(self, student_id: str) -> dict | None:
        self.refresh()
        student = next((candidate for candidate in self.db.students if candidate.id == student_id), None)
        open_case = next(
            (support_case for support_case in self.db.support_cases if support_case.student_id == student_id and support_case.case_status == "open"),
            None,
        )
        if student is None or open_case is None:
            return None
        memory_card = next((card for card in self.db.memory_cards if card.student_id == student_id and card.status == "active"), None)
        school = self.get_school(student.school_code)
        profile = student.model_dump(by_alias=True)
        dashboard = _student_dashboard(student.profile_json)
        timetable_slots = self._latest_timetable_slots_for_student(student)
        context_bundle = self.get_student_context_bundle(student_id)
        profile.update(
            {
                "gradeLabel": dashboard.get("gradeLabel") or _grade_label(student.grade),
                "studentTypeLabel": dashboard.get("studentTypeLabel") or _student_type_label(student.student_type),
                "trackLabel": dashboard.get("trackLabel") or _student_type_label(student.student_type),
                "attendanceRate": dashboard.get("attendanceRate"),
                "attendanceLabel": dashboard.get("attendanceLabel") or _attendance_label(dashboard.get("attendanceRate")),
                "strengths": _student_dashboard_list(student.profile_json, "strengths"),
                "weaknesses": _student_dashboard_list(student.profile_json, "weaknesses"),
            }
        )
        return {
            "profile": profile,
            "school": school.model_dump(by_alias=True) if school else None,
            "schoolContext": _school_context_bundle(school, self.db.school_calendar_events, timetable_slots) if school else None,
            "dashboardProfile": _dashboard_profile(student, open_case, school, memory_card, context_bundle),
            "contextBundle": context_bundle,
            "openCase": open_case.model_dump(by_alias=True),
            "memoryCard": memory_card.model_dump(by_alias=True) if memory_card else None,
            "weeklyRecords": [
                note.model_dump(by_alias=True) for note in self.db.case_notes if note.case_id == open_case.id
            ],
            "monthlySummary": {
                "repeatedProblemTypes": memory_card.learning_problem_types if memory_card else [],
                "growth": "seed 데모 기준 최근 수행 안정화",
                "stillBlocking": memory_card.next_session_cautions if memory_card else [],
            },
            "recentContents": [content.model_dump(by_alias=True) for content in self.db.mission_contents if content.student_id == student_id],
            "plannerItems": [item.model_dump(by_alias=True) for item in self.db.planner_items if item.student_id == student_id],
            "publicContextSummary": {
                "schoolCode": student.school_code,
                "schoolName": school.school_name if school else None,
                "schoolKind": school.school_kind if school else None,
                "sources": [source.source_code for source in self.db.public_data_sources],
            },
        }

    def get_student_context_bundle(self, student_id: str) -> dict | None:
        self.refresh()
        student = next((candidate for candidate in self.db.students if candidate.id == student_id), None)
        open_case = next(
            (support_case for support_case in self.db.support_cases if support_case.student_id == student_id and support_case.case_status == "open"),
            None,
        )
        if student is None or open_case is None:
            return None

        school = self.get_school(student.school_code)
        memory_card = next((card for card in self.db.memory_cards if card.student_id == student_id and card.status == "active"), None)
        notes = [note for note in self.db.case_notes if note.case_id == open_case.id]
        planner = next(
            (
                item
                for item in self.db.planner_items
                if item.student_id == student.id and item.period_type == "next_session" and item.status == "planned"
            ),
            None,
        )
        contents = [content for content in self.db.mission_contents if content.student_id == student.id]
        attempts = [attempt for attempt in self.db.attempts if attempt.student_id == student.id]
        reviews = [summary for summary in self.db.review_summaries if summary.student_id == student.id]
        timetable_slots = self._latest_timetable_slots_for_student(student)
        calendar = _upcoming_calendar_for_school(self.db.school_calendar_events, student.school_code)
        dashboard = _student_dashboard(student.profile_json)

        previous_lessons = []
        for attempt in sorted(attempts, key=lambda item: item.started_at, reverse=True)[:3]:
            content = next((candidate for candidate in contents if candidate.id == attempt.mission_content_id), None)
            review = next((candidate for candidate in reviews if candidate.attempt_id == attempt.id), None)
            previous_lessons.append(
                {
                    "contentId": content.id if content else attempt.mission_content_id,
                    "title": content.title if content else "이전 학습 콘텐츠",
                    "completedAt": attempt.completed_at,
                    "summary": review.short_summary if review else "아직 리뷰 요약이 없습니다.",
                    "accuracyRate": review.accuracy_rate if review else None,
                    "studentReviewText": _latest_reflection_text(self.db.activity_events, attempt.id),
                }
            )

        auto_context = [{"label": "학생 기록", "value": _teacher_facing_text(dashboard.get("responsePattern") or student.primary_need)}]
        if previous_lessons:
            auto_context.append({"label": "이전 수업", "value": _teacher_facing_text(previous_lessons[0]["summary"])})
        timetable_context = _timetable_context_text(timetable_slots)
        if timetable_context:
            auto_context.append({"label": "학교 시간표", "value": timetable_context})
        auto_context.append({"label": "다음 목표", "value": _teacher_facing_text(planner.goal_text if planner else open_case.current_goal)})

        return {
            "student": {
                "id": student.id,
                "name": student.display_name,
                "displayName": student.display_name,
                "grade": student.grade,
                "gradeLabel": dashboard.get("gradeLabel") or _grade_label(student.grade),
                "studentType": student.student_type,
                "studentTypeLabel": dashboard.get("studentTypeLabel") or _student_type_label(student.student_type),
                "trackLabel": dashboard.get("trackLabel") or _student_type_label(student.student_type),
            },
            "caseSummary": {
                "caseId": open_case.id,
                "currentGoal": _teacher_facing_text(open_case.current_goal),
                "primaryNeed": _teacher_facing_text(student.primary_need),
                "supportStrategy": _teacher_facing_text(open_case.support_strategy),
                "dashboardStage": open_case.dashboard_stage,
                "dashboardStageLabel": _dashboard_stage_label(open_case.dashboard_stage),
            },
            "teacherInputs": [note.model_dump(by_alias=True) for note in sorted(notes, key=lambda item: item.created_at, reverse=True)[:5]],
            "previousLessons": previous_lessons,
            "memoryCard": memory_card.model_dump(by_alias=True) if memory_card else None,
            "schoolContext": _school_context_bundle(school, calendar, timetable_slots) if school else None,
            "autoContext": auto_context,
            "aiReadyContext": {
                "summary": _teacher_facing_text(dashboard.get("aiContextSummary") or student.primary_need),
                "mustUse": _teacher_facing_list(dashboard.get("nextSessionFocus") or []),
                "avoid": _default_ai_avoid_list(student.student_type),
                "evidenceSources": _evidence_sources(school, calendar, timetable_slots),
            },
        }

    def get_student_history(self, student_id: str, teacher_id: str | None = None) -> dict | None:
        self.refresh()
        student = next((candidate for candidate in self.db.students if candidate.id == student_id), None)
        open_case = next(
            (
                support_case
                for support_case in self.db.support_cases
                if support_case.student_id == student_id
                and support_case.case_status == "open"
                and (teacher_id is None or support_case.owner_teacher_id == teacher_id)
            ),
            None,
        )
        if student is None or open_case is None:
            return None

        attempts = [attempt for attempt in self.db.attempts if attempt.student_id == student_id]
        attempt_ids = {attempt.id for attempt in attempts}
        content_ids = {content.id for content in self.db.mission_contents if content.student_id == student_id}

        return {
            "student": student.model_dump(by_alias=True),
            "openCase": open_case.model_dump(by_alias=True),
            "caseNotes": [
                note.model_dump(by_alias=True) for note in self.db.case_notes if note.case_id == open_case.id
            ],
            "missionContents": [
                content.model_dump(by_alias=True) for content in self.db.mission_contents if content.student_id == student_id
            ],
            "attempts": [attempt.model_dump(by_alias=True) for attempt in attempts],
            "activityEvents": [
                event.model_dump(by_alias=True) for event in self.db.activity_events if event.attempt_id in attempt_ids
            ],
            "realtimeSessions": [
                session.model_dump(by_alias=True) for session in self.db.realtime_sessions if session.mission_content_id in content_ids
            ],
            "reviewSummaries": [
                summary.model_dump(by_alias=True) for summary in self.db.review_summaries if summary.student_id == student_id
            ],
        }

    def get_student_report(self, student_id: str, teacher_id: str | None = None) -> dict | None:
        self.refresh()
        student = next((candidate for candidate in self.db.students if candidate.id == student_id), None)
        open_case = next(
            (
                support_case
                for support_case in self.db.support_cases
                if support_case.student_id == student_id
                and support_case.case_status == "open"
                and (teacher_id is None or support_case.owner_teacher_id == teacher_id)
            ),
            None,
        )
        if student is None or open_case is None:
            return None

        contents_by_id = {content.id: content for content in self.db.mission_contents if content.student_id == student_id}
        attempts = [attempt for attempt in self.db.attempts if attempt.student_id == student_id]
        attempts_by_id = {attempt.id: attempt for attempt in attempts}
        reports = []

        for summary in self.db.review_summaries:
            if summary.student_id != student_id:
                continue
            attempt = attempts_by_id.get(summary.attempt_id)
            if attempt is None:
                continue
            content = contents_by_id.get(attempt.mission_content_id)
            realtime_session = next((session for session in self.db.realtime_sessions if session.attempt_id == attempt.id), None)
            activity_events = [event for event in self.db.activity_events if event.attempt_id == attempt.id]
            answer_events = [event for event in activity_events if event.event_type == "answer_submitted"]
            reflection = next((event for event in reversed(activity_events) if event.event_type == "post_practice_reflection"), None)
            wrong_count = sum(1 for event in answer_events if event.payload_json.get("isCorrect") is False)
            hint_count = sum(1 for event in answer_events if event.payload_json.get("hintUsed") is True)

            reports.append(
                {
                    "id": summary.id,
                    "studentId": summary.student_id,
                    "caseId": open_case.id,
                    "contentId": content.id if content else attempt.mission_content_id,
                    "contentTitle": content.title if content else None,
                    "attemptId": attempt.id,
                    "startedAt": attempt.started_at,
                    "completedAt": attempt.completed_at,
                    "completionRate": summary.completion_rate,
                    "accuracyRate": summary.accuracy_rate,
                    "durationSec": _duration_seconds(attempt.started_at, attempt.completed_at),
                    "answerCount": len(answer_events),
                    "wrongCount": wrong_count,
                    "hintCount": hint_count,
                    "shortSummary": summary.short_summary,
                    "wrongPatternJson": summary.wrong_pattern_json,
                    "realtimeResultJson": summary.realtime_result_json,
                    "realtimeTranscriptSummary": realtime_session.transcript_summary if realtime_session else None,
                    "reflection": reflection.payload_json if reflection else None,
                }
            )

        return {
            "student": student.model_dump(by_alias=True),
            "openCase": open_case.model_dump(by_alias=True),
            "reports": sorted(reports, key=lambda item: item["completedAt"] or item["startedAt"], reverse=True),
        }

    def get_mission_for_teacher(self, content_id: str, teacher_id: str | None = None) -> MissionContent | None:
        self.refresh()
        mission = next((content for content in self.db.mission_contents if content.id == content_id), None)
        if mission is None:
            return None
        support_case = next((case for case in self.db.support_cases if case.id == mission.case_id), None)
        if support_case is None or (teacher_id is not None and support_case.owner_teacher_id != teacher_id):
            return None
        return mission

    def approve_mission_content(
        self,
        content_id: str,
        teacher_id: str,
        approved_stage_ids: list[str],
        approved_asset_ids: list[str],
        review_note: str | None,
    ) -> MissionContent | None:
        self.refresh()
        mission = self.get_mission_for_teacher(content_id, teacher_id)
        if mission is None:
            return None
        stage_ids = {stage.id for stage in mission.stages}
        asset_ids = {asset.id for asset in mission.assets}
        if not stage_ids.issubset(set(approved_stage_ids)) or not asset_ids.issubset(set(approved_asset_ids)):
            return None
        for asset in mission.assets:
            asset.approval_status = "approved"
        mission.status = MissionStatus.APPROVED
        mission.teacher_review_summary = review_note
        mission.approved_by_user_id = teacher_id
        mission.approved_at = _now()
        self.persist()
        return mission

    def reject_mission_content(self, content_id: str, teacher_id: str, reason: str, requested_changes: list[str]) -> MissionContent | None:
        self.refresh()
        mission = self.get_mission_for_teacher(content_id, teacher_id)
        if mission is None:
            return None
        mission.status = MissionStatus.REVISION_REQUESTED
        mission.teacher_review_summary = reason
        mission.brief_json = {**mission.brief_json, "requestedChanges": requested_changes}
        self.persist()
        return mission

    def publish_mission_content(self, content_id: str, teacher_id: str) -> MissionContent | None:
        self.refresh()
        mission = self.get_mission_for_teacher(content_id, teacher_id)
        if mission is None or mission.status != MissionStatus.APPROVED:
            return None
        if any(asset.approval_status != "approved" for asset in mission.assets):
            return None
        mission.status = MissionStatus.PUBLISHED
        mission.published_at = _now()
        support_case = next((case for case in self.db.support_cases if case.id == mission.case_id), None)
        if support_case is not None:
            support_case.dashboard_stage = "learning"
        self.persist()
        return mission

    def create_review_summary_for_content(self, content_id: str, teacher_id: str | None = None) -> ReviewSummary | None:
        self.refresh()
        mission = self.get_mission_for_teacher(content_id, teacher_id)
        if mission is None:
            return None
        attempts = sorted(
            [attempt for attempt in self.db.attempts if attempt.mission_content_id == content_id],
            key=lambda item: item.started_at,
            reverse=True,
        )
        if not attempts:
            return None
        attempt = attempts[0]
        existing = next((summary for summary in self.db.review_summaries if summary.attempt_id == attempt.id), None)
        if existing is not None:
            return existing
        events = [event for event in self.db.activity_events if event.attempt_id == attempt.id]
        answer_events = [event for event in events if event.event_type == "answer_submitted"]
        correct_count = sum(1 for event in answer_events if event.payload_json.get("isCorrect") is True)
        wrong_count = sum(1 for event in answer_events if event.payload_json.get("isCorrect") is False)
        accuracy_rate = correct_count / len(answer_events) if answer_events else 0
        completion_rate = 1.0 if attempt.status == "completed" else min(max(attempt.current_step / 4, 0), 1)
        reflection = next((event.payload_json for event in reversed(events) if event.event_type == "post_practice_reflection"), None)
        realtime_session = next((session for session in self.db.realtime_sessions if session.attempt_id == attempt.id), None)
        short_summary = _build_korean_review_summary_text(completion_rate, accuracy_rate, wrong_count, reflection, realtime_session)
        summary = ReviewSummary(
            id=f"review_{uuid4()}",
            attemptId=attempt.id,
            studentId=attempt.student_id,
            completionRate=completion_rate,
            accuracyRate=accuracy_rate,
            shortSummary=short_summary,
            wrongPatternJson={
                "answerCount": len(answer_events),
                "correctCount": correct_count,
                "wrongCount": wrong_count,
                "reflection": reflection,
            },
            realtimeResultJson=realtime_session.model_dump(by_alias=True) if realtime_session else {},
        )
        self.db.review_summaries.append(summary)
        self.persist()
        return summary

    def get_latest_review_summary_for_content(self, content_id: str, teacher_id: str | None = None) -> ReviewSummary | None:
        self.refresh()
        mission = self.get_mission_for_teacher(content_id, teacher_id)
        if mission is None:
            return None
        attempts = sorted(
            [attempt for attempt in self.db.attempts if attempt.mission_content_id == content_id],
            key=lambda item: item.started_at,
            reverse=True,
        )
        for attempt in attempts:
            summaries = [summary for summary in self.db.review_summaries if summary.attempt_id == attempt.id]
            if summaries:
                return summaries[-1]
        return None

    def apply_review_summary_to_memory(self, review_id: str, teacher_id: str | None = None) -> MemoryCard | None:
        self.refresh()
        summary = next((candidate for candidate in self.db.review_summaries if candidate.id == review_id), None)
        if summary is None:
            return None
        open_case = next((case for case in self.db.support_cases if case.student_id == summary.student_id and case.case_status == "open"), None)
        if open_case is None or (teacher_id is not None and open_case.owner_teacher_id != teacher_id):
            return None
        for index, card in enumerate(self.db.memory_cards):
            if card.student_id != summary.student_id or card.status != "active":
                continue
            cautions = list(card.next_session_cautions)
            if summary.short_summary not in cautions:
                cautions.append(summary.short_summary)
            updated = card.model_copy(
                update={
                    "recent_4w_response_json": {
                        **card.recent_4w_response_json,
                        "latestReviewSummaryId": summary.id,
                        "latestReviewSummary": summary.short_summary,
                        "latestAccuracyRate": summary.accuracy_rate,
                        "latestCompletionRate": summary.completion_rate,
                    },
                    "next_session_cautions": cautions[-5:],
                    "teacher_verified_at": _now(),
                }
            )
            self.db.memory_cards[index] = updated
            self.persist()
            return updated
        return None

    def add_student_note(self, student_id: str, author_id: str, payload: dict[str, Any]) -> CaseNote | None:
        open_case = next(
            (support_case for support_case in self.db.support_cases if support_case.student_id == student_id and support_case.case_status == "open"),
            None,
        )
        if open_case is None:
            return None
        note = CaseNote(
            id=f"note_{uuid4()}",
            caseId=open_case.id,
            authorId=author_id,
            noteType=payload["noteType"],
            body=payload["body"],
            visibility=payload.get("visibility", "teacher_only"),
            createdAt=_now(),
        )
        self.db.case_notes.append(note)
        self.persist()
        return note

    def get_school(self, school_code: str | None):
        self.refresh()
        if school_code is None:
            return None
        return next((school for school in self.db.schools if school.school_code == school_code), None)

    def list_schools(self) -> list[dict]:
        self.refresh()
        return [school.model_dump(by_alias=True) for school in self.db.schools]

    def list_school_calendar_events(self, school_code: str, from_date: str | None = None, to_date: str | None = None) -> list[dict]:
        self.refresh()
        events = []
        for event in self.db.school_calendar_events:
            if event.school_code != school_code:
                continue
            if from_date and event.event_date < from_date:
                continue
            if to_date and event.event_date > to_date:
                continue
            events.append(event.model_dump(by_alias=True))
        return sorted(events, key=lambda item: item["eventDate"])

    def list_school_timetable_slots(
        self,
        school_code: str,
        timetable_date: str | None = None,
        grade: str | None = None,
        class_name: str | None = None,
    ) -> list[dict]:
        self.refresh()
        slots = []
        for slot in self.db.school_timetable_slots:
            if slot.school_code != school_code:
                continue
            if timetable_date and slot.timetable_date != timetable_date:
                continue
            if grade and slot.grade != grade:
                continue
            if class_name and slot.class_name != class_name:
                continue
            slots.append(slot.model_dump(by_alias=True))
        return sorted(slots, key=lambda item: (item["timetableDate"], item["grade"], item["className"], item["period"]))

    def get_timetable_context(
        self,
        school_code: str,
        *,
        timetable_date: str | None = None,
        grade: str | None = None,
        class_name: str | None = None,
    ) -> dict | None:
        self.refresh()
        school = self.get_school(school_code)
        if school is None:
            return None
        slots = self.list_school_timetable_slots(
            school_code,
            timetable_date=timetable_date,
            grade=grade,
            class_name=class_name,
        )
        if not slots:
            return {
                "school": school.model_dump(by_alias=True),
                "date": timetable_date,
                "grade": grade,
                "className": class_name,
                "slots": [],
                "source": {"provider": "NEIS", "cacheStatus": "empty", "retrievedAt": None},
                "orchestratorHints": ["저장된 시간표 snapshot이 없어 NEIS 동기화가 필요합니다."],
            }
        return _timetable_context_response(school.model_dump(by_alias=True), slots, requested_date=timetable_date)

    def upsert_public_school_context(
        self,
        *,
        schools: list[dict[str, Any]],
        calendar: list[dict[str, Any]],
        timetable: list[dict[str, Any]],
    ) -> dict[str, int]:
        self.refresh()
        school_models = [SchoolProfile.model_validate(item) for item in schools]
        calendar_models = [SchoolCalendarEvent.model_validate(item) for item in calendar]
        timetable_models = [SchoolTimetableSlot.model_validate(item) for item in timetable]

        school_codes = {item.school_code for item in school_models}
        event_ids = {item.id for item in calendar_models}
        timetable_ids = {item.id for item in timetable_models}

        self.db.schools = [item for item in self.db.schools if item.school_code not in school_codes] + school_models
        self.db.school_calendar_events = [item for item in self.db.school_calendar_events if item.id not in event_ids] + calendar_models
        self.db.school_timetable_slots = [item for item in self.db.school_timetable_slots if item.id not in timetable_ids] + timetable_models
        self.persist()
        return {"schools": len(school_models), "calendar": len(calendar_models), "timetable": len(timetable_models)}

    def sync_neis_timetable_cache(
        self,
        *,
        office_code: str,
        school_code: str,
        timetable_date: str,
        grade: str,
        class_name: str,
        client,
    ) -> dict[str, int]:
        result = client.sync_school_context(
            office_code=office_code,
            school_code=school_code,
            from_date=None,
            to_date=None,
            timetable_date=timetable_date,
            grade=grade,
            class_name=class_name,
        )
        return self.upsert_public_school_context(**result)

    def _latest_timetable_slots_for_student(self, student) -> list[dict]:
        dashboard = _student_dashboard(student.profile_json)
        grade = str(student.profile_json.get("gradeNumber") or _grade_number(student.grade) or "")
        class_name = str(student.profile_json.get("className") or "")
        slots = self.list_school_timetable_slots(student.school_code or "", grade=grade, class_name=class_name)
        if not slots:
            return []
        latest_date = max(slot["timetableDate"] for slot in slots)
        preferred_date = dashboard.get("preferredTimetableDate")
        active_date = preferred_date if preferred_date in {slot["timetableDate"] for slot in slots} else latest_date
        return [slot for slot in slots if slot["timetableDate"] == active_date]

    def patch_memory_card(self, student_id: str, patch: dict[str, Any]) -> MemoryCard | None:
        for index, card in enumerate(self.db.memory_cards):
            if card.student_id == student_id and card.status == "active":
                merged = card.model_copy(update={key: value for key, value in patch.items() if value is not None})
                self.db.memory_cards[index] = merged
                self.persist()
                return merged
        return None

    def list_published_missions_for_student(self, student_id: str) -> list[MissionContent]:
        self.refresh()
        return [content for content in self.db.mission_contents if content.student_id == student_id and content.status == "published"]

    def save_generated_mission_content(self, mission: MissionContent) -> MissionContent:
        self.refresh()
        if not isinstance(mission.brief_json.get("generatedAt"), str):
            mission.brief_json = {**mission.brief_json, "generatedAt": _now()}
        self.db.mission_contents = [content for content in self.db.mission_contents if content.id != mission.id]
        self.db.mission_contents.append(mission)
        self.persist()
        return mission

    def get_published_mission_for_student(self, student_id: str, content_id: str) -> MissionContent | None:
        self.refresh()
        return next(
            (
                content
                for content in self.db.mission_contents
                if content.id == content_id and content.student_id == student_id and content.status == "published"
            ),
            None,
        )

    def create_attempt(self, student_id: str, mission_content_id: str) -> ContentAttempt:
        self.refresh()
        attempt = ContentAttempt(
            id=f"attempt_{uuid4()}",
            studentId=student_id,
            missionContentId=mission_content_id,
            status="in_progress",
            currentStep=1,
            startedAt=_now(),
        )
        self.db.attempts.append(attempt)
        self.persist()
        return attempt

    def submit_stage(self, student_id: str, content_id: str, stage_id: str, attempt_id: str, answer: dict[str, Any]) -> dict | None:
        self.refresh()
        mission = self.get_published_mission_for_student(student_id, content_id)
        attempt = self.get_attempt(attempt_id)
        stage = next((candidate for candidate in mission.stages if candidate.id == stage_id), None) if mission else None
        if mission is None or stage is None or attempt is None or attempt.student_id != student_id:
            return None
        if stage.step == 4:
            return {"isRealtimeStage": True}

        result = _evaluate_answer(stage.template_json, answer)
        attempt.current_step = min(4, stage.step + 1)
        self.db.activity_events.append(
            ActivityEvent(
                id=f"event_{uuid4()}",
                attemptId=attempt.id,
                studentId=student_id,
                stageId=stage.id,
                eventType="answer_submitted",
                payloadJson={"answer": answer, "isCorrect": result["isCorrect"]},
                occurredAt=_now(),
            )
        )
        self.persist()
        return {"isRealtimeStage": False, **result, "nextStep": attempt.current_step}

    def create_realtime_session(self, student_id: str, content_id: str, stage_id: str, attempt_id: str) -> RealtimePracticeSession | None:
        self.refresh()
        mission = self.get_published_mission_for_student(student_id, content_id)
        attempt = self.get_attempt(attempt_id)
        stage = next((candidate for candidate in mission.stages if candidate.id == stage_id), None) if mission else None
        if mission is None or stage is None or attempt is None or attempt.student_id != student_id:
            return None
        if stage.step != 4 or stage.realtime_spec is None:
            return None
        session = RealtimePracticeSession(
            id=f"rt_session_{uuid4()}",
            attemptId=attempt.id,
            missionContentId=mission.id,
            stageId=stage.id,
            studentId=student_id,
            provider="openai",
            model=get_settings().openai_realtime_model,
            status="created",
            specSnapshotJson=stage.realtime_spec.model_dump(by_alias=True),
            turnCount=0,
            durationSec=0,
        )
        self.db.realtime_sessions.append(session)
        self.persist()
        return session

    def save_reflection(self, student_id: str, content_id: str, attempt_id: str, reflection_choice: str, short_text: str | None) -> dict | None:
        self.refresh()
        attempt = self.get_attempt(attempt_id)
        if attempt is None or attempt.student_id != student_id or attempt.mission_content_id != content_id:
            return None
        self.db.activity_events.append(
            ActivityEvent(
                id=f"event_{uuid4()}",
                attemptId=attempt.id,
                studentId=student_id,
                eventType="post_practice_reflection",
                payloadJson={"reflectionChoice": reflection_choice, "shortText": short_text},
                occurredAt=_now(),
            )
        )
        self.persist()
        return {"saved": True}

    def save_student_activity_event(
        self,
        student_id: str,
        content_id: str,
        attempt_id: str | None,
        stage_id: str | None,
        event_type: str,
        payload_json: dict[str, Any],
    ) -> ActivityEvent | None:
        self.refresh()
        mission = self.get_published_mission_for_student(student_id, content_id)
        if mission is None:
            return None
        if attempt_id is not None:
            attempt = self.get_attempt(attempt_id)
            if attempt is None or attempt.student_id != student_id or attempt.mission_content_id != content_id:
                return None
        if stage_id is not None and not any(stage.id == stage_id for stage in mission.stages):
            return None
        event = ActivityEvent(
            id=f"event_{uuid4()}",
            attemptId=attempt_id,
            studentId=student_id,
            stageId=stage_id,
            eventType=event_type,
            payloadJson=payload_json,
            occurredAt=_now(),
        )
        self.db.activity_events.append(event)
        self.persist()
        return event

    def save_realtime_event(self, student_id: str, session_id: str, event_type: str, payload_json: dict[str, Any]) -> ActivityEvent | None:
        self.refresh()
        session = next((candidate for candidate in self.db.realtime_sessions if candidate.id == session_id and candidate.student_id == student_id), None)
        if session is None:
            return None
        event = ActivityEvent(
            id=f"event_{uuid4()}",
            attemptId=session.attempt_id,
            studentId=student_id,
            stageId=session.stage_id,
            eventType=event_type,
            payloadJson={"realtimeSessionId": session.id, **payload_json},
            occurredAt=_now(),
        )
        self.db.activity_events.append(event)
        self.persist()
        return event

    def complete_realtime_session(
        self,
        student_id: str,
        session_id: str,
        turn_count: int,
        duration_sec: int,
        rubric_result: dict[str, Any],
        transcript_summary: str | None,
    ) -> RealtimePracticeSession | None:
        self.refresh()
        for index, session in enumerate(self.db.realtime_sessions):
            if session.id != session_id or session.student_id != student_id:
                continue
            updated = session.model_copy(
                update={
                    "status": "completed",
                    "ended_at": _now(),
                    "turn_count": turn_count,
                    "duration_sec": duration_sec,
                    "rubric_result_json": rubric_result,
                    "transcript_summary": transcript_summary,
                }
            )
            self.db.realtime_sessions[index] = updated
            self.db.activity_events.append(
                ActivityEvent(
                    id=f"event_{uuid4()}",
                    attemptId=updated.attempt_id,
                    studentId=student_id,
                    stageId=updated.stage_id,
                    eventType="realtime_session_completed",
                    payloadJson={"realtimeSessionId": updated.id, "turnCount": turn_count, "durationSec": duration_sec},
                    occurredAt=_now(),
                )
            )
            self.persist()
            return updated
        return None

    def complete_attempt(self, student_id: str, content_id: str, attempt_id: str) -> ContentAttempt | None:
        self.refresh()
        attempt = self.get_attempt(attempt_id)
        if attempt is None or attempt.student_id != student_id or attempt.mission_content_id != content_id:
            return None
        attempt.status = "completed"
        attempt.current_step = 4
        attempt.completed_at = _now()
        attempt.score_json = {"completionRate": 1}
        mission = next((content for content in self.db.mission_contents if content.id == content_id), None)
        support_case = next((case for case in self.db.support_cases if mission is not None and case.id == mission.case_id), None)
        if support_case is not None:
            support_case.dashboard_stage = "feedback"
        self.persist()
        return attempt

    def get_attempt(self, attempt_id: str) -> ContentAttempt | None:
        self.refresh()
        return next((attempt for attempt in self.db.attempts if attempt.id == attempt_id), None)

    def _create_session(self, kind: str, id: str, role: str, student_id: str | None = None) -> SessionPrincipal:
        return SessionPrincipal(
            token=f"demo.{kind}.{uuid4()}",
            kind=kind,
            id=id,
            role=role,
            studentId=student_id,
            expiresAt=(datetime.now(UTC) + timedelta(hours=12)).isoformat(),
        )


_TEACHER_TEXT_REPLACEMENTS = (
    ("teach-back realtime", "말로 다시 설명하는 실시간 발화 연습"),
    ("teach back realtime", "말로 다시 설명하는 실시간 발화 연습"),
    ("roleplay realtime", "실시간 역할 발화 연습"),
    ("realtime roleplay", "실시간 역할 발화 연습"),
    ("realtime_roleplay", "실시간 역할 발화 연습"),
    ("realtime_teach_back", "실시간으로 말로 다시 설명하기"),
    ("realtime_practice", "실시간 발화 연습"),
    ("realtime 역할극", "실시간 역할 발화 연습"),
    ("realtime 역할 연습", "실시간 역할 발화 연습"),
    ("realtime 말하기", "실시간 발화"),
    ("realtime-session API", "실시간 연습 API"),
    ("realtime 스펙", "실시간 연습 구성"),
    ("realtime 연습", "실시간 발화 연습"),
    ("teach-back", "말로 다시 설명하기"),
    ("teach_back", "말로 다시 설명하기"),
    ("mascot_teach_back", "마스코트와 말로 정리하기"),
    ("roleplay", "역할 연습"),
    ("Realtime", "실시간"),
    ("realtime", "실시간"),
)


def _teacher_facing_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value
    for source, replacement in _TEACHER_TEXT_REPLACEMENTS:
        text = text.replace(source, replacement)
    return text


def _teacher_facing_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [_teacher_facing_text(item) for item in values if isinstance(item, str)]


def _teacher_facing_context_items(items: Any) -> list[dict[str, str]]:
    if not isinstance(items, list):
        return []
    localized_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        label = item.get("label")
        value = item.get("value")
        if not isinstance(label, str) or not isinstance(value, str):
            continue
        localized_items.append({"label": _teacher_facing_text(label), "value": _teacher_facing_text(value)})
    return localized_items


def _student_dashboard(profile_json: dict[str, Any]) -> dict[str, Any]:
    dashboard = profile_json.get("dashboard")
    return dashboard if isinstance(dashboard, dict) else {}


def _grade_number(grade: str) -> str | None:
    if grade.startswith("elementary_"):
        return grade.removeprefix("elementary_")
    if grade.startswith("middle_"):
        return grade.removeprefix("middle_")
    if grade.startswith("high_"):
        return grade.removeprefix("high_")
    return None


def _grade_label(grade: str) -> str:
    number = _grade_number(grade)
    if grade.startswith("elementary_") and number:
        return f"초{number}"
    if grade.startswith("middle_") and number:
        return f"중{number}"
    if grade.startswith("high_") and number:
        return f"고{number}"
    return grade


def _student_type_label(student_type: str) -> str:
    return "일상생활 지원형" if student_type == "life_support" else "학습지원형"


def _dashboard_stage_label(stage: str) -> str:
    return {
        "initial_review": "초기 확인",
        "material_generation": "자료 생성",
        "material_review": "자료 검토",
        "learning": "학습",
        "feedback": "학습 피드백",
    }.get(stage, stage)


def _attendance_label(value: Any) -> str:
    if value is None:
        return "기록 전"
    return f"{value}%"


def _dashboard_profile(student, open_case, school, memory_card, context_bundle: dict | None) -> dict[str, Any]:
    dashboard = _student_dashboard(student.profile_json)
    auto_context = _teacher_facing_context_items(context_bundle.get("autoContext", []) if context_bundle else [])
    school_name = school.school_name if school else "학교 정보 확인 중"
    grade_label = _teacher_facing_text(dashboard.get("gradeLabel") or _grade_label(student.grade))
    track_label = _teacher_facing_text(dashboard.get("trackLabel") or _student_type_label(student.student_type))
    return {
        "headline": f"{school_name} · {grade_label} · {track_label}",
        "currentStageLabel": _dashboard_stage_label(open_case.dashboard_stage),
        "attendanceLabel": _teacher_facing_text(dashboard.get("attendanceLabel") or _attendance_label(dashboard.get("attendanceRate"))),
        "primaryNeedTitle": _teacher_facing_text(dashboard.get("primaryNeedTitle") or student.primary_need),
        "primaryNeedDetail": _teacher_facing_text(dashboard.get("primaryNeedDetail") or student.primary_need),
        "supportStrategyTitle": _teacher_facing_text(dashboard.get("supportStrategyTitle") or "지원 전략"),
        "supportStrategyDetail": _teacher_facing_text(dashboard.get("supportStrategyDetail") or open_case.support_strategy),
        "strengths": _teacher_facing_list(dashboard.get("strengths") or []),
        "weaknesses": _teacher_facing_list(dashboard.get("weaknesses") or []),
        "emotionalNote": _teacher_facing_text(dashboard.get("emotionalNote") or (memory_card.emotional_state_note if memory_card else None)),
        "responsePattern": _teacher_facing_text(dashboard.get("responsePattern")),
        "guardianCooperation": _teacher_facing_text(dashboard.get("guardianCooperation") or (memory_card.guardian_cooperation_status if memory_card else None)),
        "schoolContextNote": _teacher_facing_text(dashboard.get("schoolContextNote")),
        "nextSessionFocus": _teacher_facing_list(dashboard.get("nextSessionFocus") or []),
        "aiContextSummary": _teacher_facing_text(dashboard.get("aiContextSummary") or student.primary_need),
        "autoContext": auto_context,
    }


def _school_context_bundle(school, calendar_items: list[Any], timetable_slots: list[dict]) -> dict[str, Any]:
    calendar = [_model_or_dict(item) for item in calendar_items if _model_or_dict(item).get("schoolCode") == school.school_code]
    sorted_calendar = sorted(calendar, key=lambda item: item.get("eventDate", ""))[:5]
    latest_sync_candidates = [
        *(item.get("retrievedAt") for item in sorted_calendar if item.get("retrievedAt")),
        *(slot.get("retrievedAt") for slot in timetable_slots if slot.get("retrievedAt")),
    ]
    latest_sync = max(latest_sync_candidates) if latest_sync_candidates else None
    return {
        "school": school.model_dump(by_alias=True),
        "calendar": sorted_calendar,
        "timetable": timetable_slots,
        "timetableSummary": {
            "todaySubjects": [slot["subjectName"] for slot in timetable_slots if slot.get("subjectName")],
            "source": "NEIS_TIMETABLE_CACHE" if timetable_slots else "NEIS_TIMETABLE_EMPTY",
            "date": timetable_slots[0]["timetableDate"] if timetable_slots else None,
            "cacheStatus": "cached_snapshot" if timetable_slots else "empty",
        },
        "lastSyncedAt": latest_sync,
    }


def _model_or_dict(item: Any) -> dict[str, Any]:
    if hasattr(item, "model_dump"):
        return item.model_dump(by_alias=True)
    return item if isinstance(item, dict) else {}


def _upcoming_calendar_for_school(events: list[SchoolCalendarEvent], school_code: str | None) -> list[SchoolCalendarEvent]:
    if not school_code:
        return []
    return sorted([event for event in events if event.school_code == school_code], key=lambda item: item.event_date)[:5]


def _latest_reflection_text(events: list[ActivityEvent], attempt_id: str) -> str | None:
    for event in reversed(events):
        if event.attempt_id != attempt_id or event.event_type != "post_practice_reflection":
            continue
        text = event.payload_json.get("shortText")
        return text if isinstance(text, str) and text else None
    return None


def _timetable_context_text(slots: list[dict]) -> str | None:
    subjects = [slot.get("subjectName") for slot in slots if slot.get("subjectName")]
    if not subjects:
        return None
    date = slots[0].get("timetableDate", "최근")
    return f"{date} 시간표: {', '.join(subjects[:6])}"


def _default_ai_avoid_list(student_type: str) -> list[str]:
    common = ["진단 라벨 노출", "개인정보 노출", "이미지 안에 문제/정답 텍스트 삽입"]
    if student_type == "life_support":
        return [*common, "긴 설명문", "복잡한 선택지"]
    return [*common, "한 번에 여러 개념 설명", "정답을 먼저 알려주는 이미지"]


def _evidence_sources(school, calendar: list[Any], timetable_slots: list[dict]) -> list[dict[str, Any]]:
    sources = []
    if school:
        sources.append({"type": "school_info", "provider": "NEIS", "schoolCode": school.school_code, "sourceCode": school.source_code})
    if calendar:
        sources.append({"type": "school_schedule", "provider": "NEIS", "count": len(calendar), "sourceCode": "neis_school_schedule"})
    if timetable_slots:
        sources.append(
            {
                "type": "timetable",
                "provider": "NEIS",
                "date": timetable_slots[0].get("timetableDate"),
                "count": len(timetable_slots),
                "sourceCode": timetable_slots[0].get("sourceCode"),
            }
        )
    return sources


def _timetable_context_response(school: dict, slots: list[dict], *, requested_date: str | None) -> dict[str, Any]:
    active_date = requested_date if requested_date and any(slot["timetableDate"] == requested_date for slot in slots) else slots[0]["timetableDate"]
    active_slots = [slot for slot in slots if slot["timetableDate"] == active_date]
    retrieved_at = max((slot.get("retrievedAt") for slot in active_slots if slot.get("retrievedAt")), default=None)
    subjects = [slot["subjectName"] for slot in active_slots if slot.get("subjectName")]
    return {
        "school": school,
        "date": active_date,
        "grade": active_slots[0].get("grade") if active_slots else None,
        "className": active_slots[0].get("className") if active_slots else None,
        "slots": active_slots,
        "source": {"provider": "NEIS", "cacheStatus": "cached_snapshot", "retrievedAt": retrieved_at},
        "orchestratorHints": _orchestrator_hints_from_subjects(subjects),
    }


def _orchestrator_hints_from_subjects(subjects: list[str]) -> list[str]:
    hints = []
    joined = " ".join(subjects)
    if any(keyword in joined for keyword in ["수학", "수리"]):
        hints.append("오늘 또는 최근 시간표에 수학 흐름이 있어 학습형 콘텐츠를 학교 수업 맥락과 연결할 수 있습니다.")
    if any(keyword in joined for keyword in ["국어", "독서"]):
        hints.append("국어/읽기 수업 흐름이 있어 긴 문장 부담 학생은 지시문을 짧게 나누는 것이 좋습니다.")
    if any(keyword in joined for keyword in ["체육", "행사", "동아리"]):
        hints.append("활동량이 있는 수업 흐름이 있어 회기 시작은 짧은 성공 경험형 미션이 적합합니다.")
    if not hints:
        hints.append("저장된 시간표 snapshot을 참고하되 학생 개인 능력 판단에는 사용하지 않습니다.")
    return hints


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _mission_updated_at(content: MissionContent) -> str | None:
    generated_at = content.brief_json.get("generatedAt") if isinstance(content.brief_json, dict) else None
    candidates = [
        value
        for value in [content.published_at, content.approved_at, generated_at]
        if isinstance(value, str) and value
    ]
    return max(candidates, default=None)


def _mission_mapping_sort_key(content: MissionContent) -> tuple[str, str]:
    return (_mission_updated_at(content) or "", content.id)


def _duration_seconds(started_at: str, completed_at: str | None) -> int | None:
    if completed_at is None:
        return None
    try:
        started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        completed = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(int((completed - started).total_seconds()), 0)


def _student_dashboard_value(profile_json: dict[str, Any], key: str) -> Any:
    dashboard = profile_json.get("dashboard")
    if not isinstance(dashboard, dict):
        return None
    return dashboard.get(key)


def _student_dashboard_list(profile_json: dict[str, Any], key: str) -> list[str]:
    value = _student_dashboard_value(profile_json, key)
    if not isinstance(value, list):
        return []
    return [_teacher_facing_text(item) for item in value if isinstance(item, str)]


def _evaluate_answer(template_json: dict[str, Any], answer: dict[str, Any]) -> dict:
    correct_feedback = str(template_json.get("correctFeedback", "좋아요."))
    wrong_feedback = str(template_json.get("wrongFeedback", "다시 확인해볼까요?"))
    expected = template_json.get("answer")
    if isinstance(expected, str):
        is_correct = answer.get("choiceId") == expected
    elif isinstance(expected, dict):
        is_correct = answer.get("matches") == expected
    elif isinstance(expected, list):
        is_correct = answer.get("order") == expected
    elif isinstance(template_json.get("matches"), dict):
        is_correct = answer.get("matches") == template_json["matches"]
    elif isinstance(template_json.get("answerOrder"), list):
        is_correct = answer.get("order") == template_json["answerOrder"]
    elif isinstance(template_json.get("acceptedAnswers"), list):
        is_correct = answer in template_json["acceptedAnswers"]
    else:
        is_correct = False
    return {
        "isCorrect": is_correct,
        "feedback": correct_feedback if is_correct else wrong_feedback,
    }


def _build_korean_review_summary_text(
    completion_rate: float,
    accuracy_rate: float,
    wrong_count: int,
    reflection: dict[str, Any] | None,
    realtime_session: RealtimePracticeSession | None,
) -> str:
    parts = [f"완료율 {completion_rate:.0%}", f"정답률 {accuracy_rate:.0%}"]
    if wrong_count:
        parts.append(f"오답 {wrong_count}개")
    if reflection and reflection.get("reflectionChoice"):
        parts.append(f"회고: {reflection['reflectionChoice']}")
    if realtime_session and realtime_session.transcript_summary:
        parts.append(f"실시간 연습: {realtime_session.transcript_summary}")
    return " / ".join(parts)


def _build_review_summary_text(
    completion_rate: float,
    accuracy_rate: float,
    wrong_count: int,
    reflection: dict[str, Any] | None,
    realtime_session: RealtimePracticeSession | None,
) -> str:
    parts = [f"완료율 {completion_rate:.0%}, 정답률 {accuracy_rate:.0%}"]
    if wrong_count:
        parts.append(f"오답 {wrong_count}개")
    if reflection and reflection.get("reflectionChoice"):
        parts.append(f"회고: {reflection['reflectionChoice']}")
    if realtime_session and realtime_session.transcript_summary:
        parts.append(f"실시간 연습: {realtime_session.transcript_summary}")
    return " / ".join(parts)
