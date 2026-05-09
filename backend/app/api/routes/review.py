import json

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.ai.openai_provider import OpenAiProvider
from app.ai.prompt_registry import load_prompt
from app.ai.provider_errors import AiProviderError
from app.api.deps import get_store, require_teacher
from app.api.response import ok
from app.core.config import get_settings
from app.domain.schemas import TeacherReportCreateRequest
from app.services.store import DemoStore, SessionPrincipal

router = APIRouter(prefix="/api/review-summaries", tags=["review-summaries"])
teacher_reports_router = APIRouter(prefix="/api/teacher-reports", tags=["teacher-reports"])


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/{review_id}/report-drafts/stream")
def stream_teacher_report_draft(
    review_id: str,
    payload: dict | None = Body(default=None),
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> StreamingResponse:
    snapshot = demo_store.get_teacher_report_input_snapshot(review_id, teacher_id=principal.id if principal.role == "teacher" else None)
    if snapshot is None:
        raise HTTPException(status_code=404, detail={"code": "REVIEW_SUMMARY_NOT_FOUND", "message": "AI 리포트 초안을 만들 리뷰 요약을 찾을 수 없습니다."})
    teacher_observation = (payload or {}).get("teacherObservation")
    if not isinstance(teacher_observation, str):
        teacher_observation = ""
    settings = get_settings()
    provider = OpenAiProvider(settings)
    report_input = _teacher_report_generation_input(snapshot, teacher_observation=teacher_observation)

    def events():
        chunks: list[str] = []
        try:
            for delta in provider.stream_text_response(
                model=settings.openai_report_model,
                instructions=load_prompt("teacher_report_draft"),
                input_snapshot=report_input,
                timeout_sec=settings.openai_report_timeout_sec,
            ):
                chunks.append(delta)
                yield _sse("draft_delta", {"text": delta})
            body_markdown = "".join(chunks).strip()
            if not body_markdown:
                yield _sse("error", {"code": "REPORT_DRAFT_EMPTY", "message": "리포트 초안 본문이 비어 있습니다."})
                return
            draft = demo_store.save_teacher_report_draft_from_markdown(
                review_id=review_id,
                snapshot=snapshot,
                body_markdown=body_markdown,
                model=settings.openai_report_model,
            )
            demo_store.record_audit(
                actor_user_id=principal.id,
                student_id=draft.student_id,
                action="create_teacher_report_draft",
                resource_type="teacher_report_draft",
                resource_id=draft.id,
                payload_json={"reviewSummaryId": review_id, "model": draft.model},
            )
            yield _sse(
                "draft_metadata",
                {
                    "nextLearningSuggestions": draft.next_learning_suggestions,
                    "memoryCandidates": draft.memory_candidates,
                },
            )
            yield _sse("done", {"draftId": draft.id, "status": draft.status})
        except AiProviderError as exc:
            yield _sse("error", {"code": exc.code, "message": exc.message})
        except Exception as exc:
            yield _sse("error", {"code": "REPORT_DRAFT_STREAM_FAILED", "message": str(exc)})

    return StreamingResponse(events(), media_type="text/event-stream")


def _teacher_report_generation_input(snapshot: dict, *, teacher_observation: str) -> dict:
    summary = snapshot.get("reviewSummary") or {}
    student = snapshot.get("student") or {}
    open_case = snapshot.get("openCase") or {}
    content = snapshot.get("content") or {}
    context_brief = snapshot.get("contextBrief") or {}
    realtime_session = snapshot.get("realtimeSession") or {}
    activity_events = snapshot.get("activityEvents") or []
    reflection = _latest_student_reflection(activity_events)
    student_utterances = _student_utterances_from_transcript(realtime_session.get("transcriptSummary"))
    effective_supports = (context_brief.get("recommendedScaffolds") or [])[:4]
    missing_evidence = _missing_report_evidence(reflection=reflection, teacher_observation=teacher_observation, student_utterances=student_utterances)
    next_adjustments = _next_adjustment_candidates(
        reflection=reflection,
        student_utterances=student_utterances,
        effective_supports=effective_supports,
        context_brief=context_brief,
    )
    return {
        "student": {
            "displayName": student.get("displayName"),
            "grade": student.get("grade"),
            "studentType": student.get("studentType"),
            "currentGoal": open_case.get("currentGoal"),
        },
        "content": {
            "title": content.get("title"),
            "sessionGoal": content.get("sessionGoal"),
            "stages": content.get("stages") or [],
        },
        "performance": {
            "completionRate": summary.get("completionRate"),
            "accuracyRate": summary.get("accuracyRate"),
            "shortSummary": summary.get("shortSummary"),
            "studentReflection": reflection,
            "realtimeObservation": _realtime_learning_observation(realtime_session.get("transcriptSummary")),
        },
        "evidenceFrame": {
            "observedFacts": _compact_strings(
                [
                    _rate_fact("완료율", summary.get("completionRate")),
                    _rate_fact("정답률", summary.get("accuracyRate")),
                    f"학생 회고: {reflection}" if reflection else "",
                    f"교사 관찰: {teacher_observation.strip()}" if teacher_observation.strip() else "",
                    f"자동 기록 요약: {summary.get('shortSummary')}" if summary.get("shortSummary") else "",
                ]
            ),
            "speechEvidence": student_utterances[:4],
            "missingEvidence": missing_evidence,
            "effectiveSupports": effective_supports,
            "nextAdjustmentCandidates": next_adjustments,
        },
        "teacherObservation": teacher_observation.strip(),
        "memoryContext": {
            "summary": context_brief.get("summary"),
            "recentSuccessPatterns": context_brief.get("recentSuccessPatterns") or [],
            "recentDifficultyPatterns": context_brief.get("recentDifficultyPatterns") or [],
            "recommendedScaffolds": effective_supports,
            "avoidTopicRegression": context_brief.get("avoidTopicRegression") or [],
        },
        "recentTeacherNotes": [
            {
                "noteType": note.get("noteType"),
                "body": note.get("body"),
            }
            for note in (snapshot.get("teacherNotes") or [])[-3:]
        ],
    }


def _rate_fact(label: str, value: object) -> str:
    if not isinstance(value, int | float):
        return ""
    return f"{label} {round(float(value) * 100)}%"


def _compact_strings(items: list[str | None]) -> list[str]:
    cleaned: list[str] = []
    for item in items:
        if not item:
            continue
        text = item.strip()
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


def _student_utterances_from_transcript(transcript_summary: str | None) -> list[str]:
    if not transcript_summary:
        return []
    utterances: list[str] = []
    for part in transcript_summary.split("/"):
        cleaned = part.strip()
        if not cleaned.startswith("학생:"):
            continue
        utterance = cleaned.replace("학생:", "", 1).strip()
        if utterance and utterance not in utterances:
            utterances.append(utterance)
    return utterances


def _missing_report_evidence(*, reflection: str | None, teacher_observation: str, student_utterances: list[str]) -> list[str]:
    missing: list[str] = []
    if not reflection:
        missing.append("학생 회고가 없어 수업 직후 정서 반응은 추가 확인이 필요합니다.")
    if not teacher_observation.strip():
        missing.append("교사 관찰 기록이 없어 실제 행동 변화는 교사 확인이 필요합니다.")
    if not student_utterances:
        missing.append("학생 발화가 충분히 분리되어 기록되지 않아 말하기 정확도는 추가 확인이 필요합니다.")
    return missing


def _next_adjustment_candidates(
    *,
    reflection: str | None,
    student_utterances: list[str],
    effective_supports: list[str],
    context_brief: dict,
) -> list[str]:
    candidates: list[str] = []
    if reflection and any(term in reflection for term in ("유치", "쉬워", "시시", "재미없")):
        candidates.append("같은 지원 방식은 유지하되 상황의 현실감과 판단 난이도를 높입니다.")
    if not student_utterances:
        candidates.append("다음 수업에서 예시 문장 후 학생이 직접 말한 표현을 분리해 확인합니다.")
    if effective_supports:
        candidates.append(f"유지할 지원 방식: {', '.join(effective_supports[:3])}")
    for pattern in (context_brief.get("recentDifficultyPatterns") or [])[:2]:
        if isinstance(pattern, str) and pattern.strip():
            candidates.append(f"다음 확인 필요: {pattern.strip()}")
    return _compact_strings(candidates)[:5]


def _latest_student_reflection(events: list[dict]) -> str | None:
    for event in reversed(events):
        if event.get("eventType") != "post_practice_reflection":
            continue
        payload = event.get("payloadJson") if isinstance(event.get("payloadJson"), dict) else {}
        short_text = payload.get("shortText")
        if isinstance(short_text, str) and short_text.strip():
            return short_text.strip()
    return None


def _realtime_learning_observation(transcript_summary: str | None) -> str:
    student_lines = _student_utterances_from_transcript(transcript_summary)
    if not transcript_summary:
        return "실시간 발화 기록은 없습니다."
    if not student_lines:
        return "학생 발화가 충분히 분리되어 기록되지 않았습니다."
    return f"학생 발화 {len(student_lines)}회: {', '.join(student_lines[:3])}"


@router.post("/{review_id}/apply-to-memory")
def apply_review_summary_to_memory(
    review_id: str,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    memory_card = demo_store.apply_review_summary_to_memory(review_id, teacher_id=principal.id if principal.role == "teacher" else None)
    if memory_card is None:
        raise HTTPException(status_code=404, detail={"code": "REVIEW_SUMMARY_NOT_FOUND", "message": "메모리에 반영할 리뷰 요약을 찾을 수 없습니다."})
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=memory_card.student_id,
        action="apply_review_to_memory",
        resource_type="review_summary",
        resource_id=review_id,
        payload_json={"memoryCardId": memory_card.id},
    )
    return ok(memory_card.model_dump(by_alias=True))


@teacher_reports_router.post("")
def save_teacher_report(
    payload: TeacherReportCreateRequest,
    principal: SessionPrincipal = Depends(require_teacher),
    demo_store: DemoStore = Depends(get_store),
) -> dict:
    report = demo_store.save_teacher_report(
        draft_id=payload.draft_id,
        review_summary_id=payload.review_summary_id,
        student_id=payload.student_id,
        content_id=payload.content_id,
        teacher_body=payload.teacher_body,
        selected_memory_candidates=payload.selected_memory_candidates,
        teacher_id=principal.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail={"code": "TEACHER_REPORT_NOT_FOUND", "message": "저장할 교사 리포트 대상을 찾을 수 없습니다."})
    demo_store.record_audit(
        actor_user_id=principal.id,
        student_id=payload.student_id,
        action="save_teacher_report",
        resource_type="teacher_report",
        resource_id=report.id,
        payload_json={"reviewSummaryId": payload.review_summary_id, "memoryCandidateCount": len(payload.selected_memory_candidates)},
    )
    return ok(report.model_dump(by_alias=True))
