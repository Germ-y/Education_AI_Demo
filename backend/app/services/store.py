from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import get_settings
from app.data.demo_data import create_demo_database
from app.domain.enums import MissionStatus
from app.domain.models import ActivityEvent, CaseNote, ContentAttempt, DemoDatabase, MemoryCard, RealtimePracticeSession, ReviewSummary
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
            self.repository.replace_database(self.db)

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
                }
                for content in self.db.mission_contents
            ],
        }

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
            latest_content = next((content for content in self.db.mission_contents if content.student_id == student.id), None)
            planner = next(
                (
                    item
                    for item in self.db.planner_items
                    if item.student_id == student.id and item.period_type == "next_session" and item.status == "planned"
                ),
                None,
            )
            students.append(
                {
                    "studentId": student.id,
                    "displayName": student.display_name,
                    "grade": student.grade,
                    "schoolCode": student.school_code,
                    "schoolName": school.school_name if school else None,
                    "studentType": student.student_type,
                    "primaryNeed": student.primary_need,
                    "latestContentStatus": latest_content.status if latest_content else "none",
                    "nextSessionSuggestion": planner.goal_text if planner else "다음 회기 목표를 설정해 주세요.",
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
        return {
            "profile": student.model_dump(by_alias=True),
            "school": school.model_dump(by_alias=True) if school else None,
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
        events = [event for event in self.db.activity_events if event.attempt_id == attempt.id]
        answer_events = [event for event in events if event.event_type == "answer_submitted"]
        correct_count = sum(1 for event in answer_events if event.payload_json.get("isCorrect") is True)
        wrong_count = sum(1 for event in answer_events if event.payload_json.get("isCorrect") is False)
        accuracy_rate = correct_count / len(answer_events) if answer_events else 0
        completion_rate = 1.0 if attempt.status == "completed" else min(max(attempt.current_step / 4, 0), 1)
        reflection = next((event.payload_json for event in reversed(events) if event.event_type == "post_practice_reflection"), None)
        realtime_session = next((session for session in self.db.realtime_sessions if session.attempt_id == attempt.id), None)
        short_summary = _build_review_summary_text(completion_rate, accuracy_rate, wrong_count, reflection, realtime_session)
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
        attempt_ids = {attempt.id for attempt in self.db.attempts if attempt.mission_content_id == content_id}
        summaries = [summary for summary in self.db.review_summaries if summary.attempt_id in attempt_ids]
        return summaries[-1] if summaries else None

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


def _now() -> str:
    return datetime.now(UTC).isoformat()


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
