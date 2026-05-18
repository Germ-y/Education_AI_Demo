from datetime import UTC, datetime, timedelta
from pathlib import Path
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
    PlannerItem,
    RealtimePracticeSession,
    ReviewSummary,
    SchoolCalendarEvent,
    SchoolProfile,
    SchoolTimetableSlot,
    Student,
    StudentAccount,
    StudentContextBrief,
    StudentSupportIntakeSource,
    StudentSupportProfile,
    SupportCase,
    TeacherReport,
    TeacherReportDraft,
)
from app.domain.schemas import ContentAsset, ContentStagePatch, MissionContent, StudentRegistrationRequest
from app.repositories.demo_repository import DemoRepository

CONTEXT_BRIEF_REFRESH_INTERVAL = timedelta(days=7)


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
                    **_mission_progress_mapping(content, self.db.attempts),
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
                    "caseId": open_case_by_student_id[student.id].id,
                    "openCaseId": open_case_by_student_id[student.id].id,
                    "caseStatus": open_case_by_student_id[student.id].case_status,
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
                    "statusLabel": stage_label,
                    "supportStrategy": _teacher_facing_text(open_case_by_student_id[student.id].support_strategy),
                    "summaryLine": _teacher_facing_text(dashboard.get("summaryLine") or student.primary_need),
                    "aiContextSummary": _teacher_facing_text(dashboard.get("aiContextSummary") or student.primary_need),
                    "nextSessionSuggestion": _teacher_facing_text(planner.goal_text if planner else "다음 회기 목표를 설정해 주세요."),
                }
            )
        return students

    def create_teacher_student(
        self,
        payload: StudentRegistrationRequest,
        *,
        teacher_id: str,
        organization_id: str,
        school: SchoolProfile,
    ) -> dict:
        self.refresh()
        existing_student = next(
            (
                student
                for student in self.db.students
                if student.display_name == payload.display_name and student.school_code == school.school_code and student.status == "active"
            ),
            None,
        )
        if existing_student is not None:
            return {
                "student": self.get_student_case_file(existing_student.id),
                "created": False,
                "accessCode": next(
                    (account.access_code for account in self.db.student_accounts if account.student_id == existing_student.id and account.status == "active"),
                    None,
                ),
            }

        student_id = f"student_{_safe_id_segment(payload.display_name)}_{uuid4().hex[:8]}"
        case_id = f"case_{student_id}"
        grade = _normalize_registration_grade(payload.grade)
        grade_number = payload.grade_number or _grade_number(grade) or ""
        class_name = payload.class_name or ""
        strengths = _registration_strengths(payload)
        weaknesses = _registration_weaknesses(payload)
        preferred_supports = _registration_preferred_supports(payload)
        support_intake = _registration_support_intake(payload)
        learning_response = support_intake.get("learningResponse") if isinstance(support_intake.get("learningResponse"), dict) else {}
        checklist_summary = support_intake.get("checklistSummary") if isinstance(support_intake.get("checklistSummary"), dict) else {}
        derived_support_hints = _registration_support_hints(
            _list_value(learning_response.get("effectiveSupports")),
            _list_value(checklist_summary.get("calmingSupports")),
            _list_value(checklist_summary.get("communicationNeeds")),
            payload.student_type,
        )
        track_label = payload.track_label or _registration_track_label(payload)
        initial_requested_topic = _registration_goal_text(payload.current_goal)
        primary_need = _registration_support_focus(payload)
        dashboard = {
            "attendanceRate": None,
            "gradeLabel": _grade_label(grade),
            "studentTypeLabel": _student_type_label(payload.student_type),
            "trackLabel": track_label,
            "statusLabel": "자료 생성 전",
            "attendanceLabel": "기록 전",
            "summaryLine": primary_need,
            "primaryNeedTitle": "현재 지원 목표",
            "primaryNeedDetail": primary_need,
            "supportStrategyTitle": "수업 설계 힌트",
            "supportStrategyDetail": _registration_support_strategy(payload),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "emotionalNote": payload.observation_note,
            "responsePattern": _registration_response_pattern(payload),
            "guardianCooperation": support_intake.get("guardianShareNote"),
            "schoolContextNote": "NEIS 학교 기본정보를 연결했습니다. 시간표 날짜와 반 정보가 있으면 시간표 snapshot도 함께 참고합니다.",
            "nextSessionFocus": [primary_need, *derived_support_hints[:2]],
            "aiContextSummary": _registration_ai_context_summary(payload, track_label, primary_need),
            "supportIntakeSummary": support_intake.get("checklistSummary", {}),
            "initialRequestedTopic": initial_requested_topic,
        }
        student = Student(
            id=student_id,
            organizationId=organization_id,
            externalKey=f"registered_{student_id}",
            displayName=payload.display_name,
            grade=grade,
            schoolCode=school.school_code,
            studentType=payload.student_type,
            primaryNeed=primary_need,
            profileJson={
                "ageBand": _registration_age_band(payload),
                "gradeNumber": grade_number,
                "className": class_name,
                "readingLoad": learning_response.get("readingLoad") or "medium",
                "choiceCountLimit": learning_response.get("choiceCountLimit") or _registration_choice_count_limit(payload.student_type, preferred_supports),
                "registration": {
                    "observationNote": payload.observation_note,
                    "preferredSupports": preferred_supports,
                    "initialRequestedTopic": initial_requested_topic,
                    "supportIntakeSummary": support_intake.get("checklistSummary", {}),
                    "createdAt": _now(),
                    "source": "teacher_registration",
                },
                "dashboard": dashboard,
            },
        )
        support_case = SupportCase(
            id=case_id,
            studentId=student_id,
            ownerTeacherId=teacher_id,
            caseStatus="open",
            currentGoal=primary_need,
            dashboardStage="material_generation",
            supportStrategy=dashboard["supportStrategyDetail"],
            openedAt=_now(),
        )
        memory_card = MemoryCard(
            id=f"memory_{student_id}",
            studentId=student_id,
            caseId=case_id,
            version=1,
            learningProblemTypes=[primary_need],
            recent4wResponseJson={
                "registrationObservation": payload.observation_note,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "preferredSupports": preferred_supports,
                "supportIntake": support_intake,
            },
            emotionalStateNote=payload.observation_note,
            effectiveExplanationStyles=preferred_supports,
            frequentBlockingUnits=weaknesses[:4],
            guardianCooperationStatus=None,
            nextSessionCautions=weaknesses[:4],
            teacherVerifiedAt=_now(),
            status="active",
        )
        planner = PlannerItem(
            id=f"planner_{student_id}_next",
            studentId=student_id,
            caseId=case_id,
            periodType="next_session",
            goalText=primary_need,
            checklistJson={"source": "student_registration", "preferredSupports": preferred_supports},
            status="planned",
        )
        intake_source = StudentSupportIntakeSource(
            id=f"support_intake_{student_id}_{uuid4().hex[:8]}",
            studentId=student_id,
            sourceType="teacher_registration",
            payloadJson={
                "registration": payload.model_dump(by_alias=True),
                "supportIntake": support_intake,
                "school": school.model_dump(by_alias=True),
            },
            createdAt=_now(),
        )
        context_brief = _build_context_brief(
            student=student,
            open_case=support_case,
            memory_card=memory_card,
            support_profile=None,
            reports=[],
            status="dirty",
            source_json={"trigger": "student_registration", "supportIntakeSourceId": intake_source.id},
        )
        account = StudentAccount(
            id=f"student_account_{student_id}",
            studentId=student_id,
            accessCode=_new_student_access_code(self.db.student_accounts),
            status="active",
        )
        self.db.students.append(student)
        self.db.support_cases.append(support_case)
        self.db.memory_cards.append(memory_card)
        self.db.planner_items.append(planner)
        self.db.student_support_intake_sources.append(intake_source)
        self.db.student_context_briefs.append(context_brief)
        self.db.student_accounts.append(account)
        self.persist()
        return {"student": self.get_student_case_file(student_id), "created": True, "accessCode": account.access_code}

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
        support_profile = self.get_confirmed_support_profile(student_id)
        latest_support_draft = self.get_latest_support_profile_draft(student_id)
        context_brief = self.get_student_context_brief(student_id)
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
            "dashboardProfile": _dashboard_profile(student, open_case, school, memory_card, context_bundle, support_profile),
            "contextBundle": context_bundle,
            "supportProfileDraft": latest_support_draft.model_dump(by_alias=True) if latest_support_draft else None,
            "supportProfile": support_profile.model_dump(by_alias=True) if support_profile else None,
            "contextBrief": context_brief.model_dump(by_alias=True) if context_brief else None,
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
            "recentContents": [
                content.model_dump(by_alias=True)
                for content in _recent_contents_for_student(self.db.mission_contents, student_id)
            ],
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
        support_profile = self.get_confirmed_support_profile(student_id)
        context_brief = self.get_student_context_brief(student_id)
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
            "supportProfile": support_profile.model_dump(by_alias=True) if support_profile else None,
            "contextBrief": context_brief.model_dump(by_alias=True) if context_brief else None,
            "autoContext": auto_context,
            "aiReadyContext": {
                "summary": _teacher_facing_text(
                    context_brief.brief_text if context_brief and not context_brief.dirty else dashboard.get("aiContextSummary") or student.primary_need
                ),
                "mustUse": _teacher_facing_list(dashboard.get("nextSessionFocus") or []),
                "avoid": _default_ai_avoid_list(student.student_type),
                "evidenceSources": _evidence_sources(school, calendar, timetable_slots),
                "contextBriefId": context_brief.id if context_brief else None,
                "contextBriefDirty": context_brief.dirty if context_brief else True,
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
            if attempt.status != "completed":
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
                    "aiReportDrafts": [
                        draft.model_dump(by_alias=True)
                        for draft in self.db.teacher_report_drafts
                        if draft.review_summary_id == summary.id
                    ],
                    "teacherReports": [
                        report.model_dump(by_alias=True)
                        for report in self.db.teacher_reports
                        if report.review_summary_id == summary.id
                    ],
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
        if any(not _is_asset_ready_for_teacher_approval(asset) for asset in mission.assets):
            return None
        for asset in mission.assets:
            asset.approval_status = "approved"
        if mission.status != MissionStatus.PUBLISHED:
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

    def update_mission_content_review(self, content_id: str, teacher_id: str, stage_patches: list[ContentStagePatch]) -> MissionContent | None:
        self.refresh()
        mission = self.get_mission_for_teacher(content_id, teacher_id)
        if mission is None or mission.status in {MissionStatus.GENERATING, MissionStatus.ARCHIVED}:
            return None

        patches_by_stage_id = {patch.stage_id: patch for patch in stage_patches}
        updated_stages = []
        for stage in mission.stages:
            patch = patches_by_stage_id.get(stage.id)
            if patch is None:
                updated_stages.append(stage)
                continue

            template_json = dict(stage.template_json)
            if patch.question is not None:
                template_json["question"] = patch.question
                if "missionText" in template_json:
                    template_json["missionText"] = patch.question

            if patch.choices is not None and isinstance(template_json.get("choices"), list):
                template_json["choices"] = _merge_choice_texts(template_json["choices"], patch.choices)

            realtime_spec = stage.realtime_spec
            if realtime_spec is not None and patch.realtime_student_goal is not None:
                realtime_spec = realtime_spec.model_copy(update={"student_goal": patch.realtime_student_goal})

            updated_stages.append(
                stage.model_copy(
                    update={
                        "student_instruction": patch.student_instruction
                        if patch.student_instruction is not None
                        else stage.student_instruction,
                        "template_json": template_json,
                        "realtime_spec": realtime_spec,
                    },
                ),
            )

        mission.stages = updated_stages
        mission.teacher_review_summary = "교사 직접 수정 저장"
        self.persist()
        return mission

    def publish_mission_content(self, content_id: str, teacher_id: str) -> MissionContent | None:
        self.refresh()
        mission = self.get_mission_for_teacher(content_id, teacher_id)
        if mission is None or mission.status not in {MissionStatus.APPROVED, MissionStatus.PUBLISHED, MissionStatus.ARCHIVED}:
            return None
        if any(not _is_asset_ready_for_student_publish(asset) for asset in mission.assets):
            return None
        published_at = _now()
        superseded_content_ids = []
        for content in self.db.mission_contents:
            if (
                content.id != mission.id
                and content.student_id == mission.student_id
                and content.case_id == mission.case_id
                and content.status == MissionStatus.PUBLISHED
            ):
                superseded_content_ids.append(content.id)
                content.status = MissionStatus.ARCHIVED
                content.brief_json = _append_content_deployment_history(
                    content.brief_json,
                    {
                        "event": "superseded",
                        "supersededAt": published_at,
                        "replacedByContentId": mission.id,
                        "teacherId": teacher_id,
                    },
                )
        mission.status = MissionStatus.PUBLISHED
        mission.published_at = published_at
        mission.brief_json = _append_content_deployment_history(
            mission.brief_json,
            {
                "event": "published",
                "publishedAt": published_at,
                "teacherId": teacher_id,
                "replacedContentIds": superseded_content_ids,
            },
        )
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
        attempts = _sort_attempts_for_review_summary(
            [attempt for attempt in self.db.attempts if attempt.mission_content_id == content_id]
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
        self.mark_context_brief_dirty(summary.student_id, source={"trigger": "review_summary_created", "reviewSummaryId": summary.id})
        self.persist()
        return summary

    def get_latest_review_summary_for_content(self, content_id: str, teacher_id: str | None = None) -> ReviewSummary | None:
        self.refresh()
        mission = self.get_mission_for_teacher(content_id, teacher_id)
        if mission is None:
            return None
        attempts = _sort_attempts_for_review_summary(
            [attempt for attempt in self.db.attempts if attempt.mission_content_id == content_id]
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
            summary_needs_caution = summary.completion_rate < 1 or summary.accuracy_rate < 0.9 or (summary.wrong_pattern_json.get("wrongCount") or 0) > 0
            if summary_needs_caution and summary.short_summary not in cautions:
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
                    "next_session_cautions": _memory_caution_candidates(cautions)[-5:],
                    "teacher_verified_at": _now(),
                }
            )
            self.db.memory_cards[index] = updated
            self.mark_context_brief_dirty(summary.student_id, source={"trigger": "review_summary_memory", "reviewSummaryId": summary.id})
            self.persist()
            return updated
        return None

    def get_latest_support_profile_draft(self, student_id: str) -> StudentSupportProfile | None:
        self.refresh()
        drafts = [
            profile
            for profile in self.db.student_support_profiles
            if profile.student_id == student_id and profile.status == "draft"
        ]
        return sorted(drafts, key=lambda item: item.created_at, reverse=True)[0] if drafts else None

    def get_confirmed_support_profile(self, student_id: str) -> StudentSupportProfile | None:
        self.refresh()
        confirmed = [
            profile
            for profile in self.db.student_support_profiles
            if profile.student_id == student_id and profile.status == "confirmed"
        ]
        return sorted(confirmed, key=lambda item: item.confirmed_at or item.created_at, reverse=True)[0] if confirmed else None

    def create_support_profile_draft(
        self,
        student_id: str,
        *,
        teacher_id: str,
        support_intake: dict[str, Any] | None = None,
        teacher_note: str | None = None,
        profile_json_override: dict[str, Any] | None = None,
        generated_by: str = "local_demo_ai",
    ) -> StudentSupportProfile | None:
        self.refresh()
        student = next((candidate for candidate in self.db.students if candidate.id == student_id), None)
        open_case = next((case for case in self.db.support_cases if case.student_id == student_id and case.case_status == "open"), None)
        if student is None or open_case is None or open_case.owner_teacher_id != teacher_id:
            return None
        source = self._latest_support_intake_source(student_id)
        if support_intake:
            source = StudentSupportIntakeSource(
                id=f"support_intake_{student_id}_{uuid4().hex[:8]}",
                studentId=student_id,
                sourceType="teacher_update",
                payloadJson={"supportIntake": support_intake, "teacherNote": teacher_note},
                createdAt=_now(),
            )
            self.db.student_support_intake_sources.append(source)
        if profile_json_override is not None:
            profile_json = _normalize_support_profile_draft_json(
                profile_json_override,
                intake_source=source,
                generated_by=generated_by,
            )
        else:
            profile_json = _build_support_profile_draft_json(
                student=student,
                open_case=open_case,
                intake_source=source,
                teacher_note=teacher_note,
            )
        draft = StudentSupportProfile(
            id=f"support_profile_draft_{student_id}_{uuid4().hex[:8]}",
            studentId=student_id,
            sourceIntakeId=source.id if source else None,
            status="draft",
            profileJson=profile_json,
            generatedBy=generated_by,
            createdAt=_now(),
        )
        self.db.student_support_profiles.append(draft)
        self.persist()
        return draft

    def confirm_support_profile(
        self,
        student_id: str,
        *,
        teacher_id: str,
        draft_id: str | None,
        profile_draft: dict[str, Any],
        teacher_note: str | None = None,
    ) -> StudentSupportProfile | None:
        self.refresh()
        student = next((candidate for candidate in self.db.students if candidate.id == student_id), None)
        open_case = next((case for case in self.db.support_cases if case.student_id == student_id and case.case_status == "open"), None)
        if student is None or open_case is None or open_case.owner_teacher_id != teacher_id:
            return None
        source_draft = next((profile for profile in self.db.student_support_profiles if profile.id == draft_id), None) if draft_id else None
        now = _now()
        self.db.student_support_profiles = [
            profile.model_copy(update={"status": "superseded"})
            if profile.student_id == student_id and profile.status == "confirmed"
            else profile
            for profile in self.db.student_support_profiles
        ]
        if source_draft is not None:
            self.db.student_support_profiles = [
                profile.model_copy(update={"status": "superseded"})
                if profile.id == source_draft.id
                else profile
                for profile in self.db.student_support_profiles
            ]
        confirmed = StudentSupportProfile(
            id=f"support_profile_{student_id}_{uuid4().hex[:8]}",
            studentId=student_id,
            sourceIntakeId=source_draft.source_intake_id if source_draft else None,
            status="confirmed",
            profileJson={**profile_draft, "teacherNote": teacher_note, "confirmedAt": now},
            generatedBy=source_draft.generated_by if source_draft else "teacher_confirmed",
            teacherConfirmedByUserId=teacher_id,
            createdAt=source_draft.created_at if source_draft else now,
            confirmedAt=now,
        )
        self.db.student_support_profiles.append(confirmed)
        _apply_support_profile_to_student_dashboard(student, open_case, confirmed.profile_json)
        memory_card = next((card for card in self.db.memory_cards if card.student_id == student_id and card.status == "active"), None)
        if memory_card is not None:
            _apply_support_profile_to_memory(memory_card, confirmed.profile_json)
        self.mark_context_brief_dirty(student_id, source={"trigger": "support_profile_confirmed", "supportProfileId": confirmed.id})
        self.persist()
        return confirmed

    def get_student_context_brief(self, student_id: str) -> StudentContextBrief | None:
        self.refresh()
        briefs = [brief for brief in self.db.student_context_briefs if brief.student_id == student_id]
        if not briefs:
            return None
        latest = sorted(briefs, key=lambda item: item.created_at, reverse=True)[0]
        if not latest.dirty and _is_context_brief_refresh_due(latest):
            latest = self.mark_context_brief_dirty(
                student_id,
                source={"trigger": "weekly_refresh_due", "intervalDays": CONTEXT_BRIEF_REFRESH_INTERVAL.days},
            ) or latest
            self.persist()
        return latest

    def mark_context_brief_dirty(self, student_id: str, *, source: dict[str, Any] | None = None) -> StudentContextBrief | None:
        briefs = [brief for brief in self.db.student_context_briefs if brief.student_id == student_id]
        if not briefs:
            return None
        latest = sorted(briefs, key=lambda item: item.created_at, reverse=True)[0]
        source_json = dict(latest.source_json)
        if source:
            source_json["lastDirtySource"] = source
            dirty_sources = list(source_json.get("dirtySources") or [])
            dirty_sources.append({**source, "markedAt": _now()})
            source_json["dirtySources"] = dirty_sources[-8:]
        updated = latest.model_copy(update={"dirty": True, "status": "dirty", "source_json": source_json})
        self.db.student_context_briefs = [updated if brief.id == latest.id else brief for brief in self.db.student_context_briefs]
        return updated

    def refresh_student_context_brief(
        self,
        student_id: str,
        *,
        teacher_id: str | None = None,
        brief_override: dict[str, Any] | None = None,
        model: str = "local_demo_ai",
    ) -> StudentContextBrief | None:
        self.refresh()
        student = next((candidate for candidate in self.db.students if candidate.id == student_id), None)
        open_case = next((case for case in self.db.support_cases if case.student_id == student_id and case.case_status == "open"), None)
        if student is None or open_case is None or (teacher_id is not None and open_case.owner_teacher_id != teacher_id):
            return None
        memory_card = next((card for card in self.db.memory_cards if card.student_id == student_id and card.status == "active"), None)
        support_profile = self.get_confirmed_support_profile(student_id)
        reports = [report for report in self.db.teacher_reports if report.student_id == student_id]
        brief = _build_context_brief(
            student=student,
            open_case=open_case,
            memory_card=memory_card,
            support_profile=support_profile,
            reports=reports,
            status="refreshed",
            source_json={"trigger": "manual_refresh", "reportCount": len(reports)},
        )
        if brief_override is not None:
            brief = brief.model_copy(
                update={
                    "brief_text": str(brief_override.get("briefText") or brief.brief_text),
                    "reading_load": str(brief_override.get("readingLoad") or brief.reading_load),
                    "choice_count": _safe_int(brief_override.get("choiceCount"), brief.choice_count),
                    "recent_success_patterns": _list_value(brief_override.get("recentSuccessPatterns"))[:8],
                    "recent_difficulty_patterns": _list_value(brief_override.get("recentDifficultyPatterns"))[:8],
                    "recommended_scaffolds": _list_value(brief_override.get("recommendedScaffolds"))[:8],
                    "avoid_topic_regression": _list_value(brief_override.get("avoidTopicRegression"))[:6],
                    "source_watermark": str(brief_override.get("sourceWatermark") or brief.source_watermark),
                    "source_json": {
                        **brief.source_json,
                        "aiGenerated": True,
                        "model": model,
                    },
                    "model": model,
                }
            )
        self.db.student_context_briefs = [item for item in self.db.student_context_briefs if item.student_id != student_id]
        self.db.student_context_briefs.append(brief)
        self.persist()
        return brief

    def create_teacher_report_draft(self, review_id: str, *, teacher_id: str | None = None) -> TeacherReportDraft | None:
        self.refresh()
        snapshot = self._teacher_report_input_snapshot(review_id, teacher_id=teacher_id)
        if snapshot is None:
            return None
        draft_body, suggestions, memory_candidates = _build_teacher_report_draft_text(snapshot)
        draft = TeacherReportDraft(
            id=f"report_draft_{uuid4()}",
            reviewSummaryId=review_id,
            studentId=snapshot["student"]["id"],
            contentId=snapshot["content"]["id"],
            status="completed",
            bodyMarkdown=draft_body,
            nextLearningSuggestions=suggestions,
            memoryCandidates=memory_candidates,
            inputSnapshotJson=snapshot,
            model="local_demo_ai",
            createdAt=_now(),
            completedAt=_now(),
        )
        self.db.teacher_report_drafts.append(draft)
        self.persist()
        return draft

    def get_teacher_report_input_snapshot(self, review_id: str, *, teacher_id: str | None = None) -> dict[str, Any] | None:
        self.refresh()
        return self._teacher_report_input_snapshot(review_id, teacher_id=teacher_id)

    def save_teacher_report_draft_from_markdown(
        self,
        *,
        review_id: str,
        snapshot: dict[str, Any],
        body_markdown: str,
        model: str,
    ) -> TeacherReportDraft:
        _, suggestions, memory_candidates = _build_teacher_report_draft_text(snapshot)
        draft = TeacherReportDraft(
            id=f"report_draft_{uuid4()}",
            reviewSummaryId=review_id,
            studentId=snapshot["student"]["id"],
            contentId=snapshot["content"]["id"],
            status="completed",
            bodyMarkdown=body_markdown.strip(),
            nextLearningSuggestions=suggestions,
            memoryCandidates=memory_candidates,
            inputSnapshotJson=snapshot,
            model=model,
            createdAt=_now(),
            completedAt=_now(),
        )
        self.db.teacher_report_drafts.append(draft)
        self.persist()
        return draft

    def save_teacher_report(
        self,
        *,
        draft_id: str | None,
        review_summary_id: str,
        student_id: str,
        content_id: str,
        teacher_body: str,
        selected_memory_candidates: list[str],
        teacher_id: str,
    ) -> TeacherReport | None:
        self.refresh()
        open_case = next((case for case in self.db.support_cases if case.student_id == student_id and case.case_status == "open"), None)
        summary = next((candidate for candidate in self.db.review_summaries if candidate.id == review_summary_id), None)
        if open_case is None or open_case.owner_teacher_id != teacher_id or summary is None or summary.student_id != student_id:
            return None
        clean_memory_candidates = _clean_memory_candidates(selected_memory_candidates)
        report = TeacherReport(
            id=f"teacher_report_{uuid4()}",
            draftId=draft_id,
            reviewSummaryId=review_summary_id,
            studentId=student_id,
            contentId=content_id,
            teacherBody=teacher_body,
            selectedMemoryCandidates=clean_memory_candidates,
            createdByUserId=teacher_id,
            createdAt=_now(),
        )
        self.db.teacher_reports.append(report)
        memory_card = next((card for card in self.db.memory_cards if card.student_id == student_id and card.status == "active"), None)
        if memory_card is not None:
            _apply_teacher_report_to_memory(memory_card, report)
        self.mark_context_brief_dirty(student_id, source={"trigger": "teacher_report_saved", "teacherReportId": report.id})
        self.persist()
        return report

    def _latest_support_intake_source(self, student_id: str) -> StudentSupportIntakeSource | None:
        sources = [source for source in self.db.student_support_intake_sources if source.student_id == student_id]
        return sorted(sources, key=lambda item: item.created_at, reverse=True)[0] if sources else None

    def _teacher_report_input_snapshot(self, review_id: str, *, teacher_id: str | None = None) -> dict[str, Any] | None:
        summary = next((candidate for candidate in self.db.review_summaries if candidate.id == review_id), None)
        if summary is None:
            return None
        student = next((candidate for candidate in self.db.students if candidate.id == summary.student_id), None)
        open_case = next((case for case in self.db.support_cases if case.student_id == summary.student_id and case.case_status == "open"), None)
        attempt = next((candidate for candidate in self.db.attempts if candidate.id == summary.attempt_id), None)
        content = next((candidate for candidate in self.db.mission_contents if attempt and candidate.id == attempt.mission_content_id), None)
        if student is None or open_case is None or attempt is None or content is None:
            return None
        if teacher_id is not None and open_case.owner_teacher_id != teacher_id:
            return None
        events = [event for event in self.db.activity_events if event.attempt_id == attempt.id]
        realtime_session = next((session for session in self.db.realtime_sessions if session.attempt_id == attempt.id), None)
        return {
            "reviewSummary": summary.model_dump(by_alias=True),
            "student": student.model_dump(by_alias=True),
            "openCase": open_case.model_dump(by_alias=True),
            "attempt": attempt.model_dump(by_alias=True),
            "content": {
                "id": content.id,
                "title": content.title,
                "sessionGoal": content.session_goal,
                "stages": [
                    {
                        "step": stage.step,
                        "studentTitle": stage.student_title,
                        "studentInstruction": stage.student_instruction,
                    }
                    for stage in sorted(content.stages, key=lambda item: item.step)
                ],
            },
            "activityEvents": [event.model_dump(by_alias=True) for event in events],
            "realtimeSession": realtime_session.model_dump(by_alias=True) if realtime_session else None,
            "contextBrief": self.get_student_context_brief(summary.student_id).model_dump(by_alias=True)
            if self.get_student_context_brief(summary.student_id)
            else None,
            "teacherNotes": [
                note.model_dump(by_alias=True)
                for note in self.db.case_notes
                if note.case_id == open_case.id
            ][-5:],
        }

    def add_student_note(self, student_id: str, author_id: str, payload: dict[str, Any]) -> CaseNote | None:
        self.refresh()
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
        self.mark_context_brief_dirty(student_id, source={"trigger": "teacher_note_added", "noteId": note.id, "noteType": note.note_type})
        self.persist()
        return note

    def get_school(self, school_code: str | None):
        self.refresh()
        if school_code is None:
            return None
        return next((school for school in self.db.schools if school.school_code == school_code), None)

    def list_schools(self, q: str | None = None) -> list[dict]:
        self.refresh()
        schools = self.db.schools
        if q:
            schools = [
                school
                for school in schools
                if q in school.school_name or q in school.school_code or q in school.region_name or q in school.school_kind
            ]
        return [school.model_dump(by_alias=True) for school in schools]

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
        latest_by_case: dict[str, MissionContent] = {}
        for content in self.db.mission_contents:
            if content.student_id != student_id or content.status != MissionStatus.PUBLISHED:
                continue
            current = latest_by_case.get(content.case_id)
            if current is None or _mission_mapping_sort_key(content) > _mission_mapping_sort_key(current):
                latest_by_case[content.case_id] = content
        return sorted(latest_by_case.values(), key=_mission_mapping_sort_key, reverse=True)

    def save_generated_mission_content(self, mission: MissionContent) -> MissionContent:
        self.refresh()
        existing = next((content for content in self.db.mission_contents if content.id == mission.id), None)
        if not isinstance(mission.brief_json.get("generatedAt"), str):
            mission.brief_json = {**mission.brief_json, "generatedAt": _now()}
        self.db.mission_contents = [content for content in self.db.mission_contents if content.id != mission.id]
        self.db.mission_contents.append(mission)
        if existing is None:
            self.mark_context_brief_dirty(mission.student_id, source={"trigger": "new_content_saved", "contentId": mission.id, "status": str(mission.status)})
        self.persist()
        return mission

    def get_active_material_for_case(self, student_id: str, case_id: str) -> MissionContent | None:
        self.refresh()
        active_statuses = {MissionStatus.GENERATING, MissionStatus.TEACHER_REVIEW, MissionStatus.APPROVED}
        candidates = [
            content
            for content in self.db.mission_contents
            if content.student_id == student_id and content.case_id == case_id and content.status in active_statuses
        ]
        return max(candidates, key=_mission_mapping_sort_key, default=None)

    def get_published_mission_for_student(self, student_id: str, content_id: str) -> MissionContent | None:
        self.refresh()
        return next(
            (
                content
                for content in self.db.mission_contents
                if content.id == content_id and content.student_id == student_id and _is_deployed_for_student(content)
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

    def create_preview_realtime_session(self, content_id: str, teacher_id: str | None, stage_id: str) -> RealtimePracticeSession | None:
        self.refresh()
        mission = self.get_mission_for_teacher(content_id, teacher_id)
        stage = next((candidate for candidate in mission.stages if candidate.id == stage_id), None) if mission else None
        if mission is None or stage is None or stage.step != 4 or stage.realtime_spec is None:
            return None

        attempt = ContentAttempt(
            id=f"attempt_preview_{uuid4()}",
            studentId=mission.student_id,
            missionContentId=mission.id,
            status="in_progress",
            currentStep=4,
            startedAt=_now(),
            scoreJson={"preview": True, "teacherId": teacher_id},
        )
        session = RealtimePracticeSession(
            id=f"rt_preview_session_{uuid4()}",
            attemptId=attempt.id,
            missionContentId=mission.id,
            stageId=stage.id,
            studentId=mission.student_id,
            provider="openai",
            model=get_settings().openai_realtime_model,
            status="created",
            specSnapshotJson=stage.realtime_spec.model_dump(by_alias=True),
            turnCount=0,
            durationSec=0,
        )
        self.db.attempts.append(attempt)
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
    return _clean_teacher_phrase(text)


def _clean_teacher_phrase(text: str) -> str:
    replacements = {
        "상황 상황": "상황",
        "장면 장면": "장면",
        "환경 환경": "환경",
        "조건 조건": "조건",
    }
    cleaned = text
    for source, replacement in replacements.items():
        cleaned = cleaned.replace(source, replacement)
    return cleaned


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


def _dashboard_profile(student, open_case, school, memory_card, context_bundle: dict | None, support_profile=None) -> dict[str, Any]:
    dashboard = _student_dashboard(student.profile_json)
    confirmed_profile = support_profile.profile_json if support_profile is not None else {}
    learning_response = confirmed_profile.get("learningResponsePattern") if isinstance(confirmed_profile, dict) else None
    behavior_support = confirmed_profile.get("behaviorSupportProfile") if isinstance(confirmed_profile, dict) else None
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
        "supportProfileStatus": "confirmed" if support_profile is not None else "none",
        "lessonDesignHints": _teacher_facing_list(confirmed_profile.get("lessonDesignHints") or []) if isinstance(confirmed_profile, dict) else [],
        "learningResponsePattern": learning_response if isinstance(learning_response, dict) else None,
        "behaviorSupportProfile": behavior_support if isinstance(behavior_support, dict) else None,
        "supportCautions": _teacher_facing_list(confirmed_profile.get("supportCautions") or []) if isinstance(confirmed_profile, dict) else [],
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


def _registration_support_intake(payload: StudentRegistrationRequest) -> dict[str, Any]:
    if isinstance(payload.support_intake, dict):
        intake = dict(payload.support_intake)
        learning_response = intake.get("learningResponse") if isinstance(intake.get("learningResponse"), dict) else {}
        checklist = intake.get("checklistSummary") if isinstance(intake.get("checklistSummary"), dict) else {}
        observed_strengths = (
            _list_value(learning_response.get("observedStrengths"))
            or _list_value(checklist.get("observedStrengths"))
            or payload.strengths
        )
        effective_supports = (
            _list_value(learning_response.get("effectiveSupports"))
            or _list_value(checklist.get("effectiveSupports"))
            or payload.preferred_supports
        )
        instruction_burdens = _list_value(learning_response.get("instructionBurdens")) or _list_value(checklist.get("instructionBurdens"))
        communication_needs = _list_value(learning_response.get("communicationNeeds")) or _list_value(checklist.get("communicationNeeds"))
        hard_situations = _list_value(checklist.get("hardSituations")) or payload.weaknesses
        calming_supports = _list_value(checklist.get("calmingSupports"))
        avoid_guidance = _list_value(checklist.get("avoidGuidance"))
        normalized_learning_response = {
            **learning_response,
            "observedStrengths": observed_strengths,
            "effectiveSupports": effective_supports,
            "readingLoad": learning_response.get("readingLoad") or _registration_reading_load(hard_situations, instruction_burdens),
            "choiceCountLimit": learning_response.get("choiceCountLimit") or _registration_choice_count_limit(payload.student_type, effective_supports),
            "instructionBurdens": instruction_burdens,
            "communicationNeeds": communication_needs,
        }
        normalized_checklist = {
            **checklist,
            "observedStrengths": observed_strengths,
            "hardSituations": hard_situations,
            "effectiveSupports": effective_supports,
            "instructionBurdens": instruction_burdens,
            "communicationNeeds": communication_needs,
            "calmingSupports": calming_supports,
            "avoidGuidance": avoid_guidance,
        }
        intake.setdefault(
            "sourceBasis",
            [
                "센터 관찰 자료의 기능평가 관점",
                "QABF 행동 기능 가설 관점",
                "도전적 행동 우선순위 체크리스트 관점",
            ],
        )
        intake["learningResponse"] = normalized_learning_response
        intake["checklistSummary"] = normalized_checklist
        intake.setdefault("recommendedScaffolds", _registration_support_hints(effective_supports, calming_supports, communication_needs, payload.student_type))
        intake.setdefault("avoidGuidance", [*hard_situations, *avoid_guidance])
        return intake
    reading_load = _registration_reading_load(payload.weaknesses, [])
    choice_limit = _registration_choice_count_limit(payload.student_type, payload.preferred_supports)
    return {
        "sourceBasis": [
            "센터 관찰 자료의 기능평가 관점",
            "QABF 행동 기능 가설 관점",
            "도전적 행동 우선순위 체크리스트 관점",
        ],
        "learningResponse": {
            "observedStrengths": payload.strengths,
            "effectiveSupports": payload.preferred_supports,
            "readingLoad": reading_load,
            "choiceCountLimit": choice_limit,
            "instructionBurdens": [],
            "communicationNeeds": [],
        },
        "challengeBehaviorPriorities": [{"label": item, "priority": index + 1} for index, item in enumerate(payload.weaknesses[:5])],
        "behaviorFunctionHypotheses": [],
        "replacementSkills": [],
        "recommendedScaffolds": _registration_support_hints(payload.preferred_supports, [], [], payload.student_type),
        "avoidGuidance": payload.weaknesses,
        "teacherObservation": payload.observation_note,
        "guardianShareNote": None,
        "checklistSummary": {
            "observedStrengths": payload.strengths,
            "hardSituations": payload.weaknesses,
            "effectiveSupports": payload.preferred_supports,
            "instructionBurdens": [],
            "communicationNeeds": [],
            "calmingSupports": [],
            "avoidGuidance": [],
        },
    }


def _build_support_profile_draft_json(
    *,
    student: Student,
    open_case: SupportCase,
    intake_source: StudentSupportIntakeSource | None,
    teacher_note: str | None,
) -> dict[str, Any]:
    intake = intake_source.payload_json if intake_source else {}
    registration = intake.get("registration") if isinstance(intake.get("registration"), dict) else {}
    support_intake = intake.get("supportIntake") if isinstance(intake.get("supportIntake"), dict) else {}
    learning_response = support_intake.get("learningResponse") if isinstance(support_intake.get("learningResponse"), dict) else {}
    checklist = support_intake.get("checklistSummary") if isinstance(support_intake.get("checklistSummary"), dict) else {}
    observed_strengths = (
        _list_value(learning_response.get("observedStrengths"))
        or _list_value(checklist.get("observedStrengths"))
        or _list_value(registration.get("strengths"))
        or _student_dashboard_list(student.profile_json, "strengths")
    )
    hard_situations = (
        _list_value(checklist.get("hardSituations"))
        or _list_value(registration.get("weaknesses"))
        or _student_dashboard_list(student.profile_json, "weaknesses")
    )
    effective_supports = (
        _list_value(learning_response.get("effectiveSupports"))
        or _list_value(checklist.get("effectiveSupports"))
        or _list_value(registration.get("preferredSupports"))
    )
    instruction_burdens = _list_value(learning_response.get("instructionBurdens")) or _list_value(checklist.get("instructionBurdens"))
    communication_needs = _list_value(learning_response.get("communicationNeeds")) or _list_value(checklist.get("communicationNeeds"))
    calming_supports = _list_value(checklist.get("calmingSupports"))
    recommended_scaffolds = (
        _list_value(support_intake.get("recommendedScaffolds"))
        or _registration_support_hints(effective_supports, calming_supports, communication_needs, student.student_type)
    )
    replacement_skills = _list_value(support_intake.get("replacementSkills")) or communication_needs
    behavior_hypotheses = _list_value(support_intake.get("behaviorFunctionHypotheses"))
    priority_behaviors = [
        str(item.get("label"))
        for item in _list_dict_value(support_intake.get("challengeBehaviorPriorities"))
        if item.get("label")
    ]

    if not observed_strengths:
        observed_strengths = ["짧은 첫 활동에서 반응 확인 필요"]
    if not effective_supports:
        effective_supports = ["지시를 짧게 나눔"]
    if not recommended_scaffolds:
        recommended_scaffolds = _registration_support_hints(effective_supports, calming_supports, communication_needs, student.student_type)
    if student.student_type == "learning_focus":
        replacement_skills = _learning_strategy_skills(
            hard_situations=hard_situations,
            effective_supports=effective_supports,
            communication_needs=communication_needs,
        )
    elif not replacement_skills:
        replacement_skills = ["도움 요청하기", "순서 확인하기"]

    choice_limit = (
        learning_response.get("choiceCountLimit")
        or student.profile_json.get("choiceCountLimit")
        or _registration_choice_count_limit(student.student_type, effective_supports)
    )
    reading_load = (
        learning_response.get("readingLoad")
        or student.profile_json.get("readingLoad")
        or _registration_reading_load(hard_situations, instruction_burdens)
    )
    can_be_hard = _dedupe([*hard_situations, *instruction_burdens])[:5] or ["긴 설명 뒤 바로 시작하기"]

    if student.student_type == "learning_focus":
        lesson_hint = (
            f"수업은 {', '.join(recommended_scaffolds[:2])}을 먼저 적용해 핵심 단서와 풀이 순서를 확인하는 흐름으로 시작합니다. "
            f"{', '.join(can_be_hard[:2])}은 한 번에 처리하지 않도록 문제 조건을 짧게 나눕니다."
        )
    else:
        lesson_hint = (
            f"관찰된 강점은 {', '.join(observed_strengths[:2])}입니다. "
            f"수업에서는 {', '.join(recommended_scaffolds[:2])}을 먼저 적용해 {', '.join(can_be_hard[:2])} 부담을 줄입니다."
        )
    if teacher_note:
        lesson_hint = f"{lesson_hint} 교사 메모: {teacher_note.strip()}"

    return {
        "profileVersion": "support_profile_v1",
        "draftLabel": "수업 설계 초안",
        "lessonDesignHints": [lesson_hint, "현재 지원 초점은 수업 방식 조정에만 활용하고, 콘텐츠 주제는 생성 요청을 우선합니다."],
        "learningResponsePattern": {
            "worksWell": observed_strengths[:5],
            "canBeHard": can_be_hard,
            "choiceCountLimit": int(choice_limit) if str(choice_limit).isdigit() else 2,
            "readingLoad": str(reading_load),
            "explanationStyle": "짧은 문장으로 한 단계씩 확인",
        },
        "behaviorSupportProfile": {
            "priorityBehaviors": priority_behaviors,
            "functionHypotheses": behavior_hypotheses,
            "replacementSkills": replacement_skills,
            "recommendedScaffolds": recommended_scaffolds[:5],
        },
        "strengths": [_registration_sentence(item, positive=True) for item in observed_strengths[:5]],
        "supportCautions": [_registration_sentence(item, positive=False) for item in can_be_hard[:5]],
        "source": {
            "intakeSourceId": intake_source.id if intake_source else None,
            "generatedBy": "local_demo_ai",
            "rawRecordPreserved": True,
        },
    }


def _normalize_support_profile_draft_json(
    profile_json: dict[str, Any],
    *,
    intake_source: StudentSupportIntakeSource | None,
    generated_by: str,
) -> dict[str, Any]:
    learning_response = profile_json.get("learningResponsePattern") if isinstance(profile_json.get("learningResponsePattern"), dict) else {}
    behavior_profile = profile_json.get("behaviorSupportProfile") if isinstance(profile_json.get("behaviorSupportProfile"), dict) else {}
    source = profile_json.get("source") if isinstance(profile_json.get("source"), dict) else {}
    return {
        "profileVersion": "support_profile_v1",
        "draftLabel": str(profile_json.get("draftLabel") or "수업 설계 초안"),
        "lessonDesignHints": _list_value(profile_json.get("lessonDesignHints"))[:4],
        "learningResponsePattern": {
            "worksWell": _list_value(learning_response.get("worksWell"))[:6],
            "canBeHard": _list_value(learning_response.get("canBeHard"))[:6],
            "choiceCountLimit": _safe_int(learning_response.get("choiceCountLimit"), 2),
            "readingLoad": str(learning_response.get("readingLoad") or "medium"),
            "explanationStyle": str(learning_response.get("explanationStyle") or "짧은 단계로 확인"),
        },
        "behaviorSupportProfile": {
            "priorityBehaviors": _list_value(behavior_profile.get("priorityBehaviors"))[:6],
            "functionHypotheses": _list_value(behavior_profile.get("functionHypotheses"))[:6],
            "replacementSkills": _list_value(behavior_profile.get("replacementSkills"))[:6],
            "recommendedScaffolds": _list_value(behavior_profile.get("recommendedScaffolds"))[:6],
        },
        "strengths": _list_value(profile_json.get("strengths"))[:6],
        "supportCautions": _list_value(profile_json.get("supportCautions"))[:6],
        "source": {
            **source,
            "intakeSourceId": intake_source.id if intake_source else source.get("intakeSourceId"),
            "generatedBy": generated_by,
            "rawRecordPreserved": True,
        },
    }


def _apply_support_profile_to_student_dashboard(student: Student, open_case: SupportCase, profile_json: dict[str, Any]) -> None:
    dashboard = dict(_student_dashboard(student.profile_json))
    hints = _list_value(profile_json.get("lessonDesignHints"))
    response_pattern = profile_json.get("learningResponsePattern") if isinstance(profile_json.get("learningResponsePattern"), dict) else {}
    behavior_profile = profile_json.get("behaviorSupportProfile") if isinstance(profile_json.get("behaviorSupportProfile"), dict) else {}
    strengths = _list_value(profile_json.get("strengths")) or dashboard.get("strengths") or []
    cautions = _list_value(profile_json.get("supportCautions")) or dashboard.get("weaknesses") or []
    scaffolds = _list_value(behavior_profile.get("recommendedScaffolds")) or _list_value(response_pattern.get("worksWell"))

    dashboard.update(
        {
            "primaryNeedTitle": "현재 지원 목표",
            "primaryNeedDetail": _support_focus_from_support_profile(student, open_case, profile_json, dashboard),
            "supportStrategyTitle": "학습 반응 패턴",
            "supportStrategyDetail": hints[0] if hints else _teacher_facing_text(open_case.support_strategy),
            "strengths": strengths,
            "weaknesses": cautions,
            "responsePattern": hints[0] if hints else dashboard.get("responsePattern"),
            "nextSessionFocus": [_support_focus_from_support_profile(student, open_case, profile_json, dashboard), *scaffolds[:3]],
            "aiContextSummary": _context_summary_from_support_profile(student, open_case, profile_json),
            "supportProfileStatus": "confirmed",
        }
    )
    student.profile_json = {**student.profile_json, "dashboard": dashboard, "supportProfile": profile_json}
    open_case.support_strategy = hints[0] if hints else open_case.support_strategy


def _apply_support_profile_to_memory(memory_card: MemoryCard, profile_json: dict[str, Any]) -> None:
    response_pattern = profile_json.get("learningResponsePattern") if isinstance(profile_json.get("learningResponsePattern"), dict) else {}
    behavior_profile = profile_json.get("behaviorSupportProfile") if isinstance(profile_json.get("behaviorSupportProfile"), dict) else {}
    memory_card.recent_4w_response_json = {
        **memory_card.recent_4w_response_json,
        "supportProfile": profile_json,
        "supportProfileConfirmedAt": profile_json.get("confirmedAt"),
    }
    memory_card.effective_explanation_styles = _dedupe(
        [*memory_card.effective_explanation_styles, *_list_value(response_pattern.get("worksWell")), *_list_value(behavior_profile.get("recommendedScaffolds"))]
    )[-8:]
    memory_card.next_session_cautions = _dedupe([*memory_card.next_session_cautions, *_list_value(profile_json.get("supportCautions"))])[-8:]
    memory_card.teacher_verified_at = _now()


def _context_summary_from_support_profile(student: Student, open_case: SupportCase, profile_json: dict[str, Any]) -> str:
    response_pattern = profile_json.get("learningResponsePattern") if isinstance(profile_json.get("learningResponsePattern"), dict) else {}
    works_well = _list_value(response_pattern.get("worksWell"))
    can_be_hard = _list_value(response_pattern.get("canBeHard"))
    return (
        f"{student.display_name} 학생은 {', '.join(works_well[:2]) or '짧은 단서'}에서 시작이 안정적입니다. "
        f"{', '.join(can_be_hard[:2]) or '긴 설명'}은 부담이 될 수 있어 지원 방식 조정에만 반영합니다. "
        "새 콘텐츠 주제는 선생님 생성 요청을 우선합니다."
    )


def _support_focus_from_support_profile(
    student: Student,
    open_case: SupportCase,
    profile_json: dict[str, Any],
    dashboard: dict[str, Any],
) -> str:
    response_pattern = profile_json.get("learningResponsePattern") if isinstance(profile_json.get("learningResponsePattern"), dict) else {}
    behavior_profile = profile_json.get("behaviorSupportProfile") if isinstance(profile_json.get("behaviorSupportProfile"), dict) else {}
    hints = _dedupe(_list_value(profile_json.get("lessonDesignHints")))
    can_be_hard = _dedupe(_list_value(response_pattern.get("canBeHard")))[:2]
    replacement_skills = _dedupe(_list_value(behavior_profile.get("replacementSkills")))[:2]
    existing = _teacher_facing_text(dashboard.get("primaryNeedDetail") or student.primary_need)

    if hints:
        return hints[0]
    if student.student_type == "life_support":
        situation = ", ".join(can_be_hard) if can_be_hard else "낯선 생활 상황"
        expression = ", ".join(replacement_skills) if replacement_skills else "도움 요청이나 확인 표현"
        return f"{situation}에서는 먼저 단서를 확인하고, {expression}을 짧게 연습합니다."
    if can_be_hard:
        return "핵심 단서를 먼저 확인하고, 짧은 단계로 개념을 설명합니다."
    return existing


def _build_context_brief(
    *,
    student: Student,
    open_case: SupportCase,
    memory_card: MemoryCard | None,
    support_profile: StudentSupportProfile | None,
    reports: list[TeacherReport],
    status: str,
    source_json: dict[str, Any],
) -> StudentContextBrief:
    profile_json = support_profile.profile_json if support_profile else student.profile_json.get("supportProfile", {})
    response_pattern_candidate = profile_json.get("learningResponsePattern") if isinstance(profile_json, dict) else None
    behavior_profile_candidate = profile_json.get("behaviorSupportProfile") if isinstance(profile_json, dict) else None
    response_pattern = response_pattern_candidate if isinstance(response_pattern_candidate, dict) else {}
    behavior_profile = behavior_profile_candidate if isinstance(behavior_profile_candidate, dict) else {}
    reading_load = str(response_pattern.get("readingLoad") or student.profile_json.get("readingLoad") or "low")
    choice_count_value = response_pattern.get("choiceCountLimit") or student.profile_json.get("choiceCountLimit") or 2
    choice_count = int(choice_count_value) if str(choice_count_value).isdigit() else 2
    recent_candidates = _clean_memory_candidates(
        [_abstract_context_pattern(candidate) for report in reports[-3:] for candidate in report.selected_memory_candidates]
    )
    recent_cautions = _memory_caution_candidates(recent_candidates)
    recent_success_candidates = [candidate for candidate in recent_candidates if candidate not in recent_cautions]
    profile_success_patterns = [_abstract_context_pattern(pattern) for pattern in _list_value(response_pattern.get("worksWell"))]
    profile_scaffold_patterns = [_abstract_context_pattern(pattern) for pattern in _list_value(behavior_profile.get("recommendedScaffolds"))]
    memory_style_patterns = _clean_memory_candidates(memory_card.effective_explanation_styles if memory_card else [])
    success_patterns = _dedupe([
        *[pattern for pattern in recent_success_candidates if not _is_presentation_scaffold(pattern)],
        *[pattern for pattern in profile_success_patterns if not _is_presentation_scaffold(pattern)],
        *[pattern for pattern in memory_style_patterns if not _is_presentation_scaffold(pattern)],
    ])[:6]
    difficulty_patterns = _memory_caution_candidates(
        _dedupe([
            *[_abstract_context_pattern(pattern) for pattern in _list_value(response_pattern.get("canBeHard"))],
            *recent_cautions,
            *[_abstract_context_pattern(pattern) for pattern in (memory_card.next_session_cautions if memory_card else [])],
        ])
    )[:6]
    scaffolds = _dedupe([
        *profile_scaffold_patterns,
        *[pattern for pattern in profile_success_patterns if _is_presentation_scaffold(pattern)],
        *[pattern for pattern in recent_success_candidates if _is_presentation_scaffold(pattern)],
        *[pattern for pattern in memory_style_patterns if _is_presentation_scaffold(pattern)],
    ])[:6]
    difficulty_patterns = [pattern for pattern in difficulty_patterns if pattern not in success_patterns]
    avoid_topics = _build_avoid_topic_regression(memory_card, current_goal=open_case.current_goal)
    reading_load_label = _reading_load_label(reading_load)
    strength_text = _join_context_items(success_patterns[:2]) or "짧은 첫 활동"
    stable_basis_text = _join_context_items(success_patterns[:2]) or "짧은 단서"
    caution_text = _join_context_items(difficulty_patterns[:2]) or "긴 설명 뒤 첫 행동 시작"
    scaffold_text = _join_support_phrases(scaffolds[:2]) or "예시 먼저 보기"
    brief_text = (
        f"{student.display_name} 학생은 {strength_text} 같은 강점이 관찰됩니다. "
        f"이전 수업과 관찰 기록을 보면 {stable_basis_text} 같은 조건에서 안정적입니다. "
        f"읽기 부담은 {reading_load_label}이며, 초기 응답 선택지는 {choice_count}개 안팎이 적합합니다. "
        f"주의할 흐름: {caution_text}. "
        f"수업 적용 힌트는 {scaffold_text}입니다. "
        f"기억장치는 새 수업 주제를 정하는 값이 아니라, 선생님 요청 주제를 다루는 제시 순서와 반응 방식을 조정하는 값입니다."
    )
    now = _now()
    return StudentContextBrief(
        id=f"context_brief_{student.id}_{uuid4().hex[:8]}",
        studentId=student.id,
        briefText=brief_text[:1800],
        studentType=_student_type_label(student.student_type),
        readingLoad=reading_load,
        choiceCount=choice_count,
        recentSuccessPatterns=success_patterns,
        recentDifficultyPatterns=difficulty_patterns,
        recommendedScaffolds=scaffolds,
        avoidTopicRegression=avoid_topics,
        sourceWatermark=now,
        dirty=status == "dirty",
        status="dirty" if status == "dirty" else "refreshed",
        sourceJson=source_json,
        model="local_demo_ai",
        refreshedAt=None if status == "dirty" else now,
        createdAt=now,
    )


def _join_support_phrases(values: list[str]) -> str:
    return ", ".join(_naturalize_support_phrase(value) for value in values if value)


def _join_context_items(values: list[str]) -> str:
    return ", ".join(_strip_sentence_end(value) for value in values if _strip_sentence_end(value))


def _build_avoid_topic_regression(memory_card: MemoryCard | None, *, current_goal: str) -> list[str]:
    if memory_card is None:
        return []
    current = _teacher_facing_text(current_goal).strip()
    candidates: list[str] = []
    for value in memory_card.learning_problem_types:
        text = _teacher_facing_text(str(value or "").strip())
        if not text or text == current or _is_memory_noise(text):
            continue
        abstracted = _abstract_context_pattern(text)
        if not abstracted or abstracted == current or _is_support_pattern_only(abstracted):
            continue
        candidates.append(abstracted)
    return _dedupe(candidates)[:5]


def _is_support_pattern_only(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return True
    topic_or_quality_markers = (
        "소재",
        "단원",
        "시계",
        "간식",
        "포스터",
        "피자",
        "분수",
        "영어",
        "수학",
        "덧셈",
        "문제 설명",
        "이미지",
    )
    if any(marker in text for marker in topic_or_quality_markers):
        return False
    support_markers = (
        "지시",
        "선택지",
        "예시",
        "단서",
        "읽기 부담",
        "강점",
        "설명",
        "확인",
        "도움 요청",
        "행동 전에",
        "상대에게",
        "낯선 상황",
        "기다",
        "짧은",
        "긴 글",
        "여러 조건",
    )
    return any(marker in text for marker in support_markers)


def _is_presentation_scaffold(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    observed_markers = ("이해", "따라 말", "설명", "구분", "찾", "완료", "정답률", "발화", "사용할 수")
    if any(marker in text for marker in observed_markers):
        return False
    scaffold_markers = (
        "예시를 먼저",
        "지시를 짧게",
        "선택지",
        "기다릴 시간",
        "기다리는 시간",
        "대답 전 기다",
        "그림 카드",
        "단계 카드",
        "순서 카드",
        "미리 보기",
        "짧은 음성",
        "한 단계씩",
        "해야 할 순서",
    )
    return any(marker in text for marker in scaffold_markers)


def _strip_sentence_end(value: str) -> str:
    return str(value or "").strip().rstrip(".!?。")


def _reading_load_label(value: str) -> str:
    labels = {"low": "낮은 편", "medium": "보통", "high": "높은 편"}
    return labels.get(value, value or "보통")


def _naturalize_support_phrase(value: str) -> str:
    text = str(value or "").strip()
    if text.endswith("줌"):
        return f"{text.removesuffix('줌')}주기"
    if text.endswith("나눔"):
        return f"{text.removesuffix('나눔')}나누기"
    if text.endswith("줄임"):
        return f"{text.removesuffix('줄임')}줄이기"
    if text.endswith("봄"):
        return f"{text.removesuffix('봄')}보기"
    if text.endswith("함"):
        return f"{text.removesuffix('함')}하기"
    return text


def _abstract_context_pattern(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = text.replace("선생님 관찰:", "").replace("교사 관찰:", "").strip()
    if "정답률" in text and "지원 방식" in text:
        supports = []
        for keyword in ("지시를 짧게 나누기", "예시를 먼저 보여주기", "선택지를 줄이기", "기다릴 시간 주기"):
            if keyword in text:
                supports.append(keyword)
        if supports:
            return f"{', '.join(supports[:3])} 조건에서 다음 시도에 연결하기"
    if "질문" in text and ("시각" in text or "단서" in text):
        return "시각 단서를 먼저 확인한 뒤 짧은 질문으로 연결하기"
    if "정답률 100" in text and "첫 단서" in text:
        return "짧은 첫 단서를 제시하면 다음 시도에 연결하기"
    if "짧은 시각 단서" in text and "끝까지 수행" in text:
        return "짧은 시각 단서와 2개 선택 구조에서 끝까지 수행하기"
    if "유치" in text:
        return "활동이 너무 단순하면 참여감이 낮아져 현실감과 판단 난이도 조정이 필요함"
    if "먼저 물어보기" in text and "실시간 발화" in text:
        return "실시간 발화에서는 먼저 물어보기 표현을 구체적으로 연습하기"
    replacements = {
        "구체 소재": "상황",
        "특정 장소": "낯선 장소",
        "특정 물건": "상황 단서",
        "바로 행동하기 전에": "행동하기 전에",
        "상대에게 먼저 묻는 표현을 사용할 수 있음": "상대에게 먼저 묻기",
        "낯선 상황은 짧은 예시 문장과 2개 선택지로 시작하면 안정적임": "낯선 상황은 짧은 예시 문장과 2개 선택지로 시작하기",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = text.replace("낯선 낯선", "낯선")
    text = text.replace(
        "낯선 상황은 짧은 예시 문장과 2개 선택지로 시작하면 안정적임",
        "낯선 상황은 짧은 예시 문장과 2개 선택지로 시작하기",
    )
    return text


def _build_teacher_report_draft_text(snapshot: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    summary = snapshot["reviewSummary"]
    content = snapshot["content"]
    realtime = snapshot.get("realtimeSession") or {}
    context_brief = snapshot.get("contextBrief") or {}
    reflection = _latest_reflection_from_snapshot(snapshot.get("activityEvents") or [])
    accuracy = round(float(summary.get("accuracyRate") or 0) * 100)
    completion = round(float(summary.get("completionRate") or 0) * 100)
    transcript_summary = _summarize_realtime_for_report(realtime.get("transcriptSummary"))
    reflection_note = _reflection_note_for_report(reflection)
    scaffold_text = _join_support_phrases((context_brief.get("recommendedScaffolds") or [])[:3]) or "짧은 예시와 단계 단서"
    next_suggestion = _next_teacher_report_suggestion(content, reflection, scaffold_text)
    memory_supports = (context_brief.get("recommendedScaffolds") or [])[:3]
    has_student_utterance = "학생이 " in transcript_summary and "주요 표현" in transcript_summary
    memory_candidates = _dedupe(
        [
            f"{scaffold_text} 조건에서 수행이 안정됨" if accuracy >= 80 and completion >= 80 else "",
            "말하기 단계에서는 학생 발화를 한 문장씩 분리해 기록하기" if has_student_utterance else "말하기 단계에서는 실제 학생 발화를 다시 확인하기",
            *memory_supports,
        ]
    )[:5]
    body = "\n".join(
        [
            "## 수업 반응",
            f"- {content['title']} 수업을 완료했습니다. 완료율은 {completion}%, 정답률은 {accuracy}%입니다.",
            f"- 학생 회고: {reflection or '저장된 회고가 없습니다.'}",
            "",
            "## 이해 변화",
            f"- 기록 요약: {summary['shortSummary']}",
            f"- 실시간 발화 관찰: {transcript_summary}",
            f"- 교사 확인 포인트: {reflection_note}",
            "",
            "## 다음 수업 제안",
            f"- {next_suggestion}",
        ]
    )
    return body, [next_suggestion], memory_candidates


def _summarize_realtime_for_report(transcript_summary: str | None) -> str:
    if not transcript_summary:
        return "실시간 발화 기록은 아직 없습니다."
    student_lines = []
    for part in transcript_summary.split("/"):
        cleaned = part.strip()
        if cleaned.startswith("학생:"):
            utterance = cleaned.replace("학생:", "", 1).strip()
            if utterance and utterance not in student_lines:
                student_lines.append(utterance)
    if not student_lines:
        return "학생 발화가 충분히 분리되어 기록되지 않아 다음 수업에서 다시 확인이 필요합니다."
    preview = ", ".join(student_lines[:3])
    return f"학생이 {len(student_lines)}회 발화했고, 주요 표현은 “{preview}”입니다."


def _reflection_note_for_report(reflection: str | None) -> str:
    if not reflection:
        return "학생 회고가 없어 수업 직후 반응을 교사가 한 번 더 확인하면 좋습니다."
    if any(term in reflection for term in ("유치", "쉬워", "시시", "재미없")):
        return "학생이 활동 수준을 낮게 느낀 반응이 있어, 다음 자료는 같은 지원 방식은 유지하되 상황의 현실감과 난이도를 높이는 편이 좋습니다."
    return "학생 회고가 남아 있어 다음 수업의 소재와 난이도 조정에 참고할 수 있습니다."


def _next_teacher_report_suggestion(content: dict[str, Any], reflection: str | None, scaffold_text: str) -> str:
    if reflection and any(term in reflection for term in ("유치", "쉬워", "시시", "재미없")):
        return f"다음 수업은 {scaffold_text} 같은 지원 방식은 유지하되, 학생 나이에 맞는 더 현실적인 상황과 한 단계 높은 판단 활동으로 조정합니다."
    return f"다음 수업은 {scaffold_text} 같은 지원 방식을 유지하면서, 이번 수업의 목표를 다른 상황으로 옮겨 적용해 봅니다."


def _latest_reflection_from_snapshot(events: list[dict[str, Any]]) -> str | None:
    for event in reversed(events):
        if event.get("eventType") != "post_practice_reflection":
            continue
        payload = event.get("payloadJson") if isinstance(event.get("payloadJson"), dict) else {}
        if isinstance(payload.get("shortText"), str) and payload["shortText"]:
            return payload["shortText"]
        if isinstance(payload.get("reflectionChoice"), str) and payload["reflectionChoice"]:
            return payload["reflectionChoice"]
    return None


def _apply_teacher_report_to_memory(memory_card: MemoryCard, report: TeacherReport) -> None:
    candidates = _clean_memory_candidates(report.selected_memory_candidates)
    caution_candidates = _memory_caution_candidates(candidates)
    memory_card.recent_4w_response_json = {
        **memory_card.recent_4w_response_json,
        "latestTeacherReportId": report.id,
        "latestTeacherReportSummary": report.teacher_body[:500],
        "selectedMemoryCandidates": candidates,
    }
    memory_card.effective_explanation_styles = _dedupe([*memory_card.effective_explanation_styles, *candidates])[-8:]
    memory_card.next_session_cautions = _memory_caution_candidates([*memory_card.next_session_cautions, *caution_candidates])[-8:]
    memory_card.teacher_verified_at = _now()


def _list_value(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_teacher_facing_text(str(item).strip()) for item in value if str(item).strip()]


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _list_dict_value(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        text = _teacher_facing_text(str(value).strip())
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _clean_memory_candidates(values: list[str]) -> list[str]:
    return _dedupe([_abstract_context_pattern(value) for value in values if not _is_memory_noise(value)])


def _is_memory_noise(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return True
    if len(text) > 260:
        return True
    noise_terms = (
        "시스템:",
        "상대:",
        "마이크 입력",
        "답변을 기다리는",
        "실시간 연습 API",
        "realtime",
        "Realtime",
        "provider",
        "session",
        "HTTP",
        "fetch",
        "오류",
        "에러",
        "timeout",
        "토큰",
        "OpenAI",
        "ElevenLabs",
        "학생 회고가",
        "수업의 소재와 난이도 조정",
        "다음번엔",
        "다음 번엔",
        "문제를 하나 만들어",
        "만들어보고 싶",
    )
    return any(term in text for term in noise_terms)


def _normalize_registration_grade(value: str) -> str:
    cleaned = value.strip()
    if cleaned.startswith(("elementary_", "middle_", "high_")):
        return cleaned
    if cleaned.startswith("초"):
        return f"elementary_{''.join(character for character in cleaned if character.isdigit()) or '1'}"
    if cleaned.startswith("중"):
        return f"middle_{''.join(character for character in cleaned if character.isdigit()) or '1'}"
    if cleaned.startswith("고"):
        return f"high_{''.join(character for character in cleaned if character.isdigit()) or '1'}"
    return cleaned


def _registration_track_label(payload: StudentRegistrationRequest) -> str:
    grade = _normalize_registration_grade(payload.grade)
    if payload.student_type == "life_support":
        return "일상생활 지원형"
    if grade.startswith("elementary_"):
        grade_number = _registration_grade_number(grade)
        return "고학년 학습지원형" if grade_number >= 4 else "저학년 학습지원형"
    if grade.startswith("middle_") or grade.startswith("high_"):
        return "고연령 학습지원형"
    return "학습지원형"


def _registration_age_band(payload: StudentRegistrationRequest) -> str:
    grade = _normalize_registration_grade(payload.grade)
    if payload.student_type == "life_support":
        return "life_support"
    if grade.startswith("elementary_"):
        return "older" if _registration_grade_number(grade) >= 4 else "younger"
    if grade.startswith("middle_") or grade.startswith("high_"):
        return "older"
    return "younger"


def _registration_grade_number(normalized_grade: str) -> int:
    digits = "".join(character for character in normalized_grade if character.isdigit())
    return int(digits or "1")


def _registration_primary_need_title(payload: StudentRegistrationRequest) -> str:
    if payload.student_type == "life_support":
        return "생활 상황 지원 수업"
    return "학습 개념 보완 수업"


def _registration_support_focus(payload: StudentRegistrationRequest) -> str:
    support_intake = _registration_support_intake(payload)
    checklist = support_intake.get("checklistSummary") if isinstance(support_intake.get("checklistSummary"), dict) else {}
    hard_situations = _dedupe(_list_value(checklist.get("hardSituations")) or _registration_weaknesses(payload))[:2]
    communication_needs = _dedupe(_list_value(checklist.get("communicationNeeds")))[:2]
    instruction_burdens = _dedupe(_list_value(checklist.get("instructionBurdens")))[:2]

    if payload.student_type == "life_support":
        situation = ", ".join(hard_situations) if hard_situations else "낯선 생활 상황"
        expression = ", ".join(communication_needs) if communication_needs else "도움 요청이나 확인 표현"
        return f"{situation}에서는 먼저 단서를 확인하고, {expression}을 짧게 연습합니다."

    if [*hard_situations, *instruction_burdens]:
        return "핵심 단서를 먼저 확인하고, 짧은 단계로 개념을 설명합니다."
    return "짧은 예시와 핵심 단서로 학습을 시작합니다."


def _registration_support_strategy(payload: StudentRegistrationRequest) -> str:
    support_intake = _registration_support_intake(payload)
    learning_response = support_intake.get("learningResponse") if isinstance(support_intake.get("learningResponse"), dict) else {}
    checklist = support_intake.get("checklistSummary") if isinstance(support_intake.get("checklistSummary"), dict) else {}
    supports = (
        _list_value(learning_response.get("effectiveSupports"))
        or _list_value(checklist.get("effectiveSupports"))
        or _registration_preferred_supports(payload)
    )
    hard_situations = _list_value(checklist.get("hardSituations")) or _registration_weaknesses(payload)
    instruction_burdens = _list_value(checklist.get("instructionBurdens"))
    calming_supports = _list_value(checklist.get("calmingSupports"))
    if supports:
        support_hints = _registration_support_hints(supports, calming_supports, _list_value(checklist.get("communicationNeeds")), payload.student_type)
        burden_candidates = _dedupe([*hard_situations, *instruction_burdens])[:2]
        burden_text = f" {', '.join(burden_candidates)} 부담을 먼저 낮춥니다." if burden_candidates else ""
        return f"관찰상 효과가 확인된 지원은 {', '.join(supports[:3])}입니다. 수업에서는 {', '.join(support_hints[:2])}을 적용합니다.{burden_text}"
    if payload.student_type == "life_support":
        return "생활 장면에서 어려워지는 조건을 먼저 확인하고, 도움 요청과 순서 확인을 수업 적용 힌트로 사용합니다."
    return "학습에서 어려워지는 조건을 먼저 확인하고, 지시를 나누어 개념 확인 순서를 안정화합니다."


def _registration_response_pattern(payload: StudentRegistrationRequest) -> str:
    support_intake = _registration_support_intake(payload)
    learning_response = support_intake.get("learningResponse") if isinstance(support_intake.get("learningResponse"), dict) else {}
    checklist = support_intake.get("checklistSummary") if isinstance(support_intake.get("checklistSummary"), dict) else {}
    strengths = _list_value(learning_response.get("observedStrengths")) or _list_value(checklist.get("observedStrengths")) or payload.strengths
    supports = (
        _list_value(learning_response.get("effectiveSupports"))
        or _list_value(checklist.get("effectiveSupports"))
        or _registration_preferred_supports(payload)
    )
    if strengths and supports:
        return f"관찰된 강점은 {', '.join(strengths[:2])}입니다. 효과가 확인된 지원은 {', '.join(supports[:2])}입니다."
    if strengths:
        return f"관찰된 강점은 {', '.join(strengths[:2])}입니다."
    return "등록 직후에는 짧은 첫 활동으로 반응을 확인하고 지원 조건을 보완합니다."


def _registration_ai_context_summary(payload: StudentRegistrationRequest, track_label: str, primary_need: str) -> str:
    note = f" {payload.observation_note}" if payload.observation_note else ""
    return f"{_grade_label(_normalize_registration_grade(payload.grade))} {track_label} 학생. 현재 지원 목표: {primary_need}.{note}"


def _registration_strengths(payload: StudentRegistrationRequest) -> list[str]:
    if payload.strengths:
        return [_registration_sentence(item, positive=True) for item in payload.strengths[:5]]
    supports = _registration_preferred_supports(payload)
    if supports:
        return [f"{support}이 제공되면 수업 참여가 안정됩니다." for support in supports[:3]]
    return ["짧은 첫 활동에서 반응을 확인해 강점을 구체화합니다."]


def _registration_weaknesses(payload: StudentRegistrationRequest) -> list[str]:
    if payload.weaknesses:
        return [_registration_sentence(item, positive=False) for item in payload.weaknesses[:5]]
    if payload.student_type == "life_support":
        return ["낯선 상황에서는 다음 행동을 확인해 주는 단서가 필요할 수 있어요."]
    return ["설명이 길어지면 중요한 조건을 놓칠 수 있어 짧은 단계화가 필요할 수 있어요."]


def _registration_preferred_supports(payload: StudentRegistrationRequest) -> list[str]:
    if payload.preferred_supports:
        return [_teacher_facing_text(item) for item in payload.preferred_supports if item][:5]
    return []


def _registration_reading_load(hard_situations: list[str], instruction_burdens: list[str]) -> str:
    joined = " ".join([*hard_situations, *instruction_burdens])
    if any(keyword in joined for keyword in ["긴 글", "긴 문장", "긴 지시", "여러 조건", "읽고 시작"]):
        return "low"
    if any(keyword in joined for keyword in ["추상", "이유", "설명"]):
        return "medium"
    return "medium"


def _registration_choice_count_limit(student_type: str, effective_supports: list[str]) -> int:
    joined = " ".join(effective_supports)
    if "선택지를 줄임" in joined or "선택지" in joined:
        return 2
    return 2 if student_type == "life_support" else 3


def _learning_strategy_skills(
    *,
    hard_situations: list[str],
    effective_supports: list[str],
    communication_needs: list[str],
) -> list[str]:
    joined = " ".join([*hard_situations, *effective_supports, *communication_needs])
    skills: list[str] = []
    if any(keyword in joined for keyword in ["조건", "긴 글", "긴 지문", "긴 문제", "단서"]):
        skills.append("문제에서 핵심 단서 표시하기")
    if any(keyword in joined for keyword in ["순서", "단계", "절차", "계산"]):
        skills.append("풀이 순서를 짧게 말하기")
    if any(keyword in joined for keyword in ["설명", "이유", "말로"]):
        skills.append("정답 이유를 한 문장으로 말하기")
    if any(keyword in joined for keyword in ["읽기", "단어", "영어", "낱말"]):
        skills.append("모르는 단어와 아는 단어 나누기")
    if any(keyword in joined for keyword in ["응용", "전이", "비슷한"]):
        skills.append("예시 문제와 다른 점 찾기")
    if any(keyword in joined for keyword in ["오류", "오답", "다시"]):
        skills.append("틀린 부분을 표시하고 한 번 더 풀기")

    skills.extend(
        item
        for item in communication_needs
        if any(keyword in item for keyword in ["다시 설명", "어디부터", "핵심 단서", "풀이", "정답 이유", "모르는 단어"])
    )
    return _dedupe(skills or ["핵심 단서 표시하기", "풀이 순서 말하기"])[:6]


def _registration_support_hints(
    effective_supports: list[str],
    calming_supports: list[str],
    communication_needs: list[str],
    student_type: str,
) -> list[str]:
    raw_items = _dedupe([*effective_supports, *calming_supports, *communication_needs])
    mapped: list[str] = []
    for item in raw_items:
        if "짧게" in item or "나눔" in item:
            mapped.append("지시를 짧게 나누기")
        elif "예시" in item or "모델" in item:
            mapped.append("예시 문제를 먼저 보여주기" if student_type == "learning_focus" else "예시를 먼저 보여주기")
        elif "선택지" in item:
            mapped.append("선택지 수 줄이기")
        elif "순서" in item:
            mapped.append("풀이 순서 먼저 확인하기" if student_type == "learning_focus" else "해야 할 순서 먼저 확인하기")
        elif "기다" in item:
            mapped.append("대답 전 기다릴 시간 주기")
        elif student_type == "learning_focus" and any(keyword in item for keyword in ["단서", "조건", "빈칸", "그림", "표"]):
            mapped.append(item)
        elif "도움 요청" in item or "다시 말" in item or "쉬기" in item or "거절" in item:
            mapped.append("확인 질문을 짧게 연습하기" if student_type == "learning_focus" else "필요한 표현을 짧게 연습하기")
        elif "안전" in item:
            if student_type == "life_support":
                mapped.append("안전 규칙 먼저 확인하기")
        elif "조용" in item:
            mapped.append("환경 자극을 줄이고 시작하기")
        elif item:
            mapped.append(item)
    if mapped:
        return _dedupe(mapped)[:6]
    if student_type == "life_support":
        return ["상황을 짧게 확인하기", "도움 요청 표현 연습하기"]
    return ["지시를 짧게 나누기", "한 단계씩 확인하기"]


def _registration_sentence(value: str, *, positive: bool) -> str:
    text = _teacher_facing_text(value)
    if text.endswith(("요.", "다.", "습니다.")):
        return text
    if positive and text.endswith("잘 찾음"):
        return f"{text.removesuffix('잘 찾음').strip()} 잘 찾아요."
    if positive and text.endswith("반응 좋음"):
        return f"{text.removesuffix('반응 좋음').strip()}에 반응이 좋아요."
    if positive and text.endswith("함"):
        return f"{text.removesuffix('함').strip()}합니다."
    if not positive and text.endswith("부담됨"):
        return f"{text.removesuffix('부담됨').strip()}부담될 수 있어요."
    if not positive and text.endswith("어려움"):
        return f"{text.removesuffix('어려움').strip()}어려울 수 있어요."
    if positive:
        return f"{text}에서 강점이 관찰됩니다."
    if text.endswith(("상황", "장면", "환경", "조건")):
        return f"{text}에서 지원이 필요할 수 있어요."
    return f"{text} 상황에서 지원이 필요할 수 있어요."


def _ensure_suggestion_sentence(value: str) -> str:
    return _registration_goal_text(value)


def _registration_goal_text(value: str) -> str:
    text = _teacher_facing_text(value.strip())
    for suffix in ("수업이 좋겠어요.", "콘텐츠가 좋겠어요.", "해보면 좋겠어요.", "하면 좋겠어요.", "좋겠어요."):
        if text.endswith(suffix):
            text = text[: -len(suffix)].strip()
            break
    if text.endswith("."):
        text = text[:-1]
    return text


def _new_student_access_code(accounts: list[StudentAccount]) -> str:
    used = {account.access_code for account in accounts}
    for index in range(1, 10000):
        code = f"STAR-{index:03d}"
        if code not in used:
            return code
    return f"STAR-{uuid4().hex[:6].upper()}"


def _safe_id_segment(value: str) -> str:
    segment = "".join(character.lower() if character.isalnum() else "_" for character in value.strip())
    segment = "_".join(part for part in segment.split("_") if part)
    return segment[:32] or "registered"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _is_context_brief_refresh_due(brief: StudentContextBrief) -> bool:
    base_time = _parse_iso_datetime(brief.refreshed_at or brief.source_watermark or brief.created_at)
    if base_time is None:
        return True
    return datetime.now(UTC) - base_time >= CONTEXT_BRIEF_REFRESH_INTERVAL


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


def _recent_contents_for_student(contents: list[MissionContent], student_id: str) -> list[MissionContent]:
    visible: dict[str, MissionContent] = {}
    for content in contents:
        if content.student_id != student_id:
            continue
        generated_at = content.brief_json.get("generatedAt") if isinstance(content.brief_json, dict) else ""
        key = "|".join(
            [
                content.case_id,
                content.title.strip(),
                str(content.status),
                generated_at if isinstance(generated_at, str) else "",
            ]
        )
        current = visible.get(key)
        if current is None or _mission_mapping_sort_key(content) >= _mission_mapping_sort_key(current):
            visible[key] = content
    return sorted(visible.values(), key=_mission_mapping_sort_key, reverse=True)


def _is_deployed_for_student(content: MissionContent) -> bool:
    return content.status == MissionStatus.PUBLISHED or (content.status == MissionStatus.ARCHIVED and bool(content.published_at))


def _append_content_deployment_history(brief_json: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    history = brief_json.get("deploymentHistory") if isinstance(brief_json, dict) else None
    return {
        **brief_json,
        "deploymentHistory": [
            *(history if isinstance(history, list) else []),
            event,
        ],
    }


def _mission_progress_mapping(content: MissionContent, attempts: list[ContentAttempt]) -> dict[str, Any]:
    content_attempts = [attempt for attempt in attempts if attempt.mission_content_id == content.id]
    latest_attempt = next(
        (
            attempt
            for attempt in sorted(content_attempts, key=lambda item: item.started_at, reverse=True)
        ),
        None,
    )
    latest_completed_attempt = next(
        (
            attempt
            for attempt in sorted(content_attempts, key=lambda item: item.completed_at or item.started_at, reverse=True)
            if attempt.status == "completed"
        ),
        None,
    )
    if latest_attempt is None:
        return {
            "latestAttemptStatus": None,
            "latestAttemptCurrentStep": None,
            "latestAttemptCompletedAt": None,
            "isCompleted": False,
        }

    return {
        "latestAttemptStatus": latest_attempt.status,
        "latestAttemptCurrentStep": latest_attempt.current_step,
        "latestAttemptCompletedAt": latest_attempt.completed_at,
        "isCompleted": latest_completed_attempt is not None,
    }


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


def _merge_choice_texts(existing_choices: Any, choice_texts: list[str]) -> list[Any]:
    if not isinstance(existing_choices, list):
        return existing_choices

    merged = []
    for index, choice in enumerate(existing_choices):
        if index >= len(choice_texts):
            merged.append(choice)
            continue

        text = choice_texts[index]
        if isinstance(choice, dict):
            merged.append({**choice, "text": text})
        else:
            merged.append(text)

    return merged


def _is_asset_ready_for_teacher_approval(asset: ContentAsset) -> bool:
    if asset.qa_status != "passed":
        return False
    return _asset_url_ready_for_review(asset.storage_url) or _asset_url_ready_for_review(asset.preview_url)


def _asset_url_ready_for_review(url: str | None) -> bool:
    if not url:
        return False
    if url.startswith("/generated/"):
        relative_path = url.removeprefix("/generated/").lstrip("/")
        return relative_path.startswith("assets/") and (Path(get_settings().generated_assets_dir) / relative_path).is_file()
    return True


def _is_asset_ready_for_student_publish(asset: ContentAsset) -> bool:
    return asset.approval_status == "approved" and _is_asset_ready_for_teacher_approval(asset)


def _sort_attempts_for_review_summary(attempts: list[ContentAttempt]) -> list[ContentAttempt]:
    def sort_key(attempt: ContentAttempt) -> tuple[int, str]:
        completed_rank = 1 if attempt.status == "completed" else 0
        timestamp = attempt.completed_at or attempt.started_at
        return completed_rank, timestamp

    return sorted(attempts, key=sort_key, reverse=True)


def _memory_caution_candidates(items: list[str]) -> list[str]:
    caution_keywords = ("어려", "부담", "주의", "필요", "놓칠", "헷갈", "흔들", "낯선", "재촉", "오답", "실패")
    hard_caution_keywords = ("어려", "부담", "주의", "필요", "놓칠", "헷갈", "흔들", "재촉", "오답", "실패")
    positive_markers = ("100%", "정답률 100", "완료율 100", "사용할 수 있음", "안정적", "선택지로 시작", "잘 ", "가능", "성공")
    cleaned: list[str] = []
    for item in items:
        text = _teacher_facing_text(str(item)).replace("상황 상황", "상황").strip()
        if not text:
            continue
        if any(marker in text for marker in positive_markers) and not any(keyword in text for keyword in hard_caution_keywords):
            continue
        if any(keyword in text for keyword in caution_keywords):
            cleaned.append(text)
    return _dedupe(cleaned)


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
