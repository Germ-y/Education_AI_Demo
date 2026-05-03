from __future__ import annotations

import json
import shutil
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import delete, select

from app.db.session import create_schema, get_session_maker
from app.domain import db_models as rows
from app.domain.schemas import MissionContent
from app.repositories.demo_repository import DemoRepository
from app.services.store import DemoStore


BASE_URL = "http://localhost:4000"
KEEP_CONTENT_ID = "content_life_bus_002"
LOG_PATH = Path("showcase-generation.log")


@dataclass(frozen=True)
class StudentPlan:
    student_id: str
    case_id: str
    content_type: str
    access_code: str
    record_goal: str
    current_goal: str
    existing_current_content_id: str | None = None


PLANS = [
    StudentPlan(
        student_id="student_learning_clock",
        case_id="case_learning_clock",
        content_type="learning_focus",
        access_code="STAR-003",
        record_goal="시계 그림을 보고 짧은 바늘부터 확인해 약속 시간을 고르는 복습 미션",
        current_goal="생활 속 약속 장면에서 시침과 분침을 차례로 보고 시간을 말해보는 새 미션",
    ),
    StudentPlan(
        student_id="student_learning_fraction",
        case_id="case_learning_fraction",
        content_type="learning_focus",
        access_code="STAR-001",
        record_goal="피자 조각 그림으로 전체와 부분을 구분하고 분모와 분자를 다시 확인하는 복습 미션",
        current_goal="간식 나누기 상황에서 분수의 전체-부분 관계를 단계별로 설명해보는 새 미션",
    ),
    StudentPlan(
        student_id="student_life_bus",
        case_id="case_life_bus",
        content_type="life_support",
        access_code="STAR-002",
        record_goal="센터에 가는 길에서 정류장 단서를 확인하고 도움 요청 문장을 다시 연습하는 복습 미션",
        current_goal="정류장에서 안부 인사하고 도움 요청하기",
        existing_current_content_id="content_life_bus_002",
    ),
]


def log(message: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {message}"
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(line + "\n")


def request_json(method: str, path: str, payload: dict[str, Any] | None = None, *, token: str | None = None, timeout: int = 600) -> Any:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: {exc.code} {detail}") from exc
    if not text:
        return None
    parsed = json.loads(text)
    if "error" in parsed:
        raise RuntimeError(f"{method} {path} failed: {parsed['error']}")
    if "detail" in parsed:
        raise RuntimeError(f"{method} {path} failed: {parsed['detail']}")
    return parsed.get("data")


def login_teacher() -> str:
    data = request_json("POST", "/api/auth/demo-login", {"role": "teacher", "email": "teacher.demo@eduyj.local"}, timeout=30)
    return data["session"]["accessToken"]


def login_student(access_code: str) -> str:
    data = request_json("POST", "/api/auth/student-access", {"accessCode": access_code}, timeout=30)
    return data["session"]["accessToken"]


def get_content(content_id: str, teacher_token: str) -> dict[str, Any]:
    return request_json("GET", f"/api/contents/{content_id}", token=teacher_token, timeout=60)


def content_ready_count(content: dict[str, Any]) -> tuple[int, int]:
    assets = content["assets"]
    ready = [asset for asset in assets if asset.get("previewUrl") or asset.get("storageUrl")]
    return len(ready), len(assets)


def generate_content(plan: StudentPlan, requested_goal: str, teacher_token: str) -> dict[str, Any]:
    role = "record" if requested_goal == plan.record_goal else "current"
    content = build_contract_content(plan, requested_goal, role)
    store = DemoStore(repository=DemoRepository(get_session_maker()))
    saved = store.save_generated_mission_content(MissionContent.model_validate(content))
    log(f"{plan.student_id}: content saved {saved.id} - {saved.title}")
    return saved.model_dump(by_alias=True)


def build_contract_content(plan: StudentPlan, requested_goal: str, role: str) -> dict[str, Any]:
    topic = topic_for(plan, requested_goal, role)
    content_id = f"content_showcase_{student_slug(plan.student_id)}_{role}"
    stage_prefix = f"stage_showcase_{student_slug(plan.student_id)}_{role}"
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    stages = build_stages(plan, content_id, stage_prefix, topic)
    assets = build_assets(plan, content_id, stages, topic)
    return {
        "id": content_id,
        "caseId": plan.case_id,
        "studentId": plan.student_id,
        "contentType": plan.content_type,
        "title": topic["title"],
        "sessionGoal": requested_goal,
        "status": "teacher_review",
        "totalSteps": 4,
        "stages": stages,
        "assets": assets,
        "briefJson": {
            "generatedAt": now,
            "source": "showcase_contract_generator_with_model_assets",
            "requestedGoal": requested_goal,
            "teacherReviewFocus": [
                "학생 화면 문장이 한국어로 자연스러운지 확인",
                "1~3단계가 정적 템플릿으로 진행되는지 확인",
                "4단계가 실시간 발화 연습인지 확인",
            ],
        },
        "teacherReviewSummary": f"{topic['title']} 데모 시연용 실제 asset 생성 콘텐츠입니다.",
        "approvedByUserId": None,
        "approvedAt": None,
        "publishedAt": None,
    }


def student_slug(student_id: str) -> str:
    return student_id.removeprefix("student_").replace("_", "-")


def topic_for(plan: StudentPlan, requested_goal: str, role: str) -> dict[str, str]:
    if plan.student_id == "student_learning_clock":
        return {
            "title": "시계 약속 시간 찾기" if role == "record" else "오늘의 시계 말하기",
            "object": "둥근 시계",
            "skill": "짧은 바늘부터 보고 시간을 고르기",
            "place": "교실",
            "correct": "3시",
            "other1": "6시",
            "other2": "9시",
            "realtime": "짧은 바늘을 먼저 보고 몇 시인지 말해보기",
        }
    if plan.student_id == "student_learning_fraction":
        return {
            "title": "피자 조각으로 분수 보기" if role == "record" else "간식 나누기 분수 설명",
            "object": "피자 조각",
            "skill": "전체와 부분을 보고 분수로 말하기",
            "place": "간식 테이블",
            "correct": "1/4",
            "other1": "1/2",
            "other2": "3/4",
            "realtime": "전체 중 한 조각이 무엇을 뜻하는지 말해보기",
        }
    return {
        "title": "버스 정류장 도움 요청 복습" if role == "record" else "정류장에서 인사하고 도움 요청하기",
        "object": "버스 정류장 안내판",
        "skill": "상황 단서를 보고 도움 요청 문장 말하기",
        "place": "버스 정류장",
        "correct": "안녕하세요, 센터 가는 버스 알려주세요.",
        "other1": "혼자 그냥 걸어갈래요.",
        "other2": "아무 말도 하지 않아요.",
        "realtime": "안내 직원에게 인사하고 도움을 요청해보기",
    }


def build_stages(plan: StudentPlan, content_id: str, stage_prefix: str, topic: dict[str, str]) -> list[dict[str, Any]]:
    if plan.content_type == "learning_focus":
        stage_roles = ["concept_intro", "basic_problem", "applied_problem", "realtime_practice"]
        template_types = ["concept_intro", "image_quiz", "applied_question", "realtime_teach_back"]
        titles = ["개념 열기", "문제 1", "문제 2", "설명해보기"]
    else:
        stage_roles = ["scenario_intro", "clue_identification", "action_selection", "realtime_practice"]
        template_types = ["scenario_intro", "highlight_clue", "action_choice", "realtime_roleplay"]
        titles = ["상황 만나기", "단서 찾기", "행동 고르기", "한 번 해보기"]

    stages: list[dict[str, Any]] = []
    for step in range(1, 5):
        stage_id = f"{stage_prefix}_{step}"
        asset_role = "stage_4_realtime" if step == 4 else f"stage_{step}"
        if step == 1:
            template_json = {
                "question": f"{topic['object']}를 보고 오늘 연습할 내용을 살펴봐요.",
                "missionText": topic["skill"],
            }
        else:
            choices = [
                {"id": "a", "text": topic["correct"]},
                {"id": "b", "text": topic["other1"]},
                {"id": "c", "text": topic["other2"]},
            ]
            template_json = {
                "question": f"{topic['place']} 장면에서 알맞은 답을 골라요.",
                "choices": choices,
                "answer": "a",
                "correctFeedback": "좋아요. 중요한 단서를 잘 보았어요.",
                "wrongFeedback": "괜찮아요. 그림 단서를 다시 천천히 봐요.",
            }
        template_json["imageAssetId"] = f"asset_{content_id}_{asset_role}"
        template_json["audioAssetId"] = f"asset_{content_id}_{asset_role}_audio"

        realtime_spec = None
        if step == 4:
            realtime_spec = {
                "id": f"rt_spec_{content_id}",
                "stageId": stage_id,
                "templateType": template_types[step - 1],
                "imageAssetId": f"asset_{content_id}_{asset_role}",
                "mode": "voice_or_text",
                "practiceTitle": titles[step - 1],
                "situationText": f"{topic['place']}에서 {topic['skill']} 연습을 합니다.",
                "aiRole": "친절한 연습 파트너",
                "openingLine": "천천히 한 문장으로 말해볼까요?",
                "studentGoal": topic["realtime"],
                "rubric": [
                    {"id": "try", "label": "말하기를 시도함", "required": True},
                    {"id": "clue", "label": "핵심 단서를 말함", "required": True},
                ],
                "allowedFeedback": ["좋아요.", "천천히 다시 말해봐도 괜찮아요."],
                "forbidden": ["진단 라벨 말하기", "개인정보 묻기", "정답을 강요하기"],
                "maxTurns": 3,
                "maxDurationSec": 120,
                "postPracticeReflection": ["쉬웠어요", "한 번 더 해볼래요", "도움이 필요해요"],
            }

        stages.append(
            {
                "id": stage_id,
                "missionContentId": content_id,
                "step": step,
                "stageRole": stage_roles[step - 1],
                "templateType": template_types[step - 1],
                "studentTitle": titles[step - 1],
                "studentInstruction": f"{topic['skill']} 활동입니다.",
                "templateJson": template_json,
                "realtimeSpec": realtime_spec,
                "sortOrder": step,
            }
        )
    return stages


def build_assets(plan: StudentPlan, content_id: str, stages: list[dict[str, Any]], topic: dict[str, str]) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    roles = [("hero", None), ("stage_1", stages[0]["id"]), ("stage_2", stages[1]["id"]), ("stage_3", stages[2]["id"]), ("stage_4_realtime", stages[3]["id"])]
    for asset_role, stage_id in roles:
        image_id = f"asset_{content_id}_{asset_role}"
        audio_id = f"asset_{content_id}_{asset_role}_audio"
        prompt = (
            f"따뜻하고 선명한 한국 교육용 일러스트. {topic['place']}에서 {topic['object']}를 중심으로 "
            f"{topic['skill']} 장면을 보여준다. 화면 안에는 문제 문장, 정답 글자, 말풍선, 개인정보가 없다. "
            "학생이 보기 편한 밝은 색감, 단순한 배경, 부드러운 캐릭터."
        )
        assets.append(
            {
                "id": image_id,
                "missionContentId": content_id,
                "stageId": stage_id,
                "assetRole": asset_role,
                "assetType": "image",
                "provider": "openai",
                "model": "gpt-image-2",
                "promptJson": {"prompt": prompt, "visualRole": asset_role, "textRenderingPolicy": "scene_only_no_problem_text"},
                "sourceText": None,
                "storageUrl": "",
                "previewUrl": None,
                "qaStatus": "pending",
                "approvalStatus": "pending",
            }
        )
        assets.append(
            {
                "id": audio_id,
                "missionContentId": content_id,
                "stageId": stage_id,
                "assetRole": asset_role,
                "assetType": "audio",
                "provider": "elevenlabs",
                "model": "eleven_multilingual_v2",
                "promptJson": None,
                "sourceText": f"{topic['title']} 활동을 시작해요. {topic['skill']}를 천천히 연습해 볼게요.",
                "storageUrl": "",
                "previewUrl": None,
                "qaStatus": "pending",
                "approvalStatus": "pending",
            }
        )
    return assets


def generate_assets(content: dict[str, Any], teacher_token: str) -> dict[str, Any]:
    content_id = content["id"]
    for asset in content["assets"]:
        if asset.get("previewUrl") or asset.get("storageUrl"):
            continue
        log(f"{content_id}: asset start {asset['id']} ({asset['assetType']} {asset['assetRole']})")
        request_json(
            "POST",
            f"/api/contents/{content_id}/assets/{asset['id']}/generate",
            token=teacher_token,
            timeout=720,
        )
        content = get_content(content_id, teacher_token)
        ready, total = content_ready_count(content)
        log(f"{content_id}: asset done {asset['id']} ({ready}/{total})")
    content = get_content(content_id, teacher_token)
    ready, total = content_ready_count(content)
    if ready != total:
        raise RuntimeError(f"{content_id}: assets incomplete {ready}/{total}")
    return content


def approve_and_publish(content: dict[str, Any], teacher_token: str) -> dict[str, Any]:
    content_id = content["id"]
    log(f"{content_id}: approve")
    content = request_json(
        "POST",
        f"/api/contents/{content_id}/approve",
        {
            "approvedStageIds": [stage["id"] for stage in content["stages"]],
            "approvedAssetIds": [asset["id"] for asset in content["assets"]],
            "reviewNote": "데모 시연용 실제 생성 콘텐츠 확인 완료",
        },
        token=teacher_token,
        timeout=60,
    )
    log(f"{content_id}: publish")
    return request_json("POST", f"/api/contents/{content_id}/publish", token=teacher_token, timeout=60)


def complete_once(content: dict[str, Any], access_code: str) -> None:
    content_id = content["id"]
    student_token = login_student(access_code)
    log(f"{content_id}: student start")
    attempt = request_json("POST", f"/api/student/missions/{content_id}/start", {"attemptId": "unused"}, token=student_token, timeout=60)
    attempt_id = attempt["id"]
    for stage in content["stages"]:
        if stage["step"] >= 4:
            continue
        log(f"{content_id}: submit stage {stage['step']}")
        request_json(
            "POST",
            f"/api/student/missions/{content_id}/stages/{stage['id']}/submit",
            {"attemptId": attempt_id, "answer": {"value": "demo"}},
            token=student_token,
            timeout=60,
        )
    log(f"{content_id}: complete attempt")
    request_json("POST", f"/api/student/missions/{content_id}/complete", {"attemptId": attempt_id}, token=student_token, timeout=60)


def summarize(teacher_token: str) -> None:
    rows = []
    for plan in PLANS:
        case_file = request_json("GET", f"/api/teacher/students/{plan.student_id}", token=teacher_token, timeout=60)
        for content in case_file["recentContents"]:
            ready, total = content_ready_count(content)
            rows.append(
                {
                    "studentId": plan.student_id,
                    "contentId": content["id"],
                    "status": content["status"],
                    "ready": f"{ready}/{total}",
                    "title": content["title"],
                    "publishedAt": content.get("publishedAt"),
                }
            )
    log("SUMMARY " + json.dumps(rows, ensure_ascii=False))


def cleanup_contents_except_keep() -> None:
    log(f"cleanup: keeping only {KEEP_CONTENT_ID}")
    create_schema()
    session_factory = get_session_maker()
    with session_factory() as session:
        content_ids = [
            row_id
            for row_id in session.scalars(select(rows.MissionContentRow.id)).all()
            if row_id != KEEP_CONTENT_ID
        ]
        if not content_ids:
            log("cleanup: no DB contents to delete")
            return

        stage_ids = session.scalars(
            select(rows.ContentStageRow.id).where(rows.ContentStageRow.mission_content_id.in_(content_ids))
        ).all()
        attempt_ids = session.scalars(
            select(rows.ContentAttemptRow.id).where(rows.ContentAttemptRow.mission_content_id.in_(content_ids))
        ).all()
        realtime_session_ids = session.scalars(
            select(rows.RealtimePracticeSessionRow.id).where(rows.RealtimePracticeSessionRow.mission_content_id.in_(content_ids))
        ).all()
        review_summary_ids = (
            session.scalars(select(rows.ReviewSummaryRow.id).where(rows.ReviewSummaryRow.attempt_id.in_(attempt_ids))).all()
            if attempt_ids
            else []
        )

        if review_summary_ids:
            session.execute(delete(rows.ReviewSummaryRow).where(rows.ReviewSummaryRow.id.in_(review_summary_ids)))
        if realtime_session_ids:
            session.execute(delete(rows.RealtimePracticeSessionRow).where(rows.RealtimePracticeSessionRow.id.in_(realtime_session_ids)))
        if attempt_ids:
            session.execute(delete(rows.ActivityEventRow).where(rows.ActivityEventRow.attempt_id.in_(attempt_ids)))
            session.execute(delete(rows.ContentAttemptRow).where(rows.ContentAttemptRow.id.in_(attempt_ids)))
        if stage_ids:
            session.execute(delete(rows.ActivityEventRow).where(rows.ActivityEventRow.stage_id.in_(stage_ids)))
        session.execute(delete(rows.ContentAssetRow).where(rows.ContentAssetRow.mission_content_id.in_(content_ids)))
        session.execute(delete(rows.ContentStageRow).where(rows.ContentStageRow.mission_content_id.in_(content_ids)))
        session.execute(delete(rows.MissionContentRow).where(rows.MissionContentRow.id.in_(content_ids)))
        session.execute(delete(rows.AuditLogRow).where(rows.AuditLogRow.resource_id.in_(content_ids)))
        for support_case in session.scalars(select(rows.SupportCaseRow)).all():
            support_case.dashboard_stage = "material_generation"
        session.commit()

    assets_root = Path("generated/assets")
    if assets_root.exists():
        for child in assets_root.iterdir():
            if child.is_dir() and child.name != KEEP_CONTENT_ID:
                shutil.rmtree(child)
                log(f"cleanup: removed generated assets {child}")
    log(f"cleanup: deleted DB contents {content_ids}")


def main() -> int:
    LOG_PATH.write_text("", encoding="utf-8")
    cleanup_contents_except_keep()
    teacher_token = login_teacher()
    generated_records: list[tuple[StudentPlan, dict[str, Any]]] = []
    current_contents: list[tuple[StudentPlan, dict[str, Any]]] = []

    for plan in PLANS:
        record = generate_content(plan, plan.record_goal, teacher_token)
        record = generate_assets(record, teacher_token)
        record = approve_and_publish(record, teacher_token)
        complete_once(record, plan.access_code)
        generated_records.append((plan, record))

        if plan.existing_current_content_id:
            current = get_content(plan.existing_current_content_id, teacher_token)
            current = generate_assets(current, teacher_token)
            current_contents.append((plan, current))
        else:
            current = generate_content(plan, plan.current_goal, teacher_token)
            current = generate_assets(current, teacher_token)
            current_contents.append((plan, current))

    for plan, current in current_contents:
        published = approve_and_publish(current, teacher_token)
        log(f"{plan.student_id}: current published {published['id']}")

    summarize(teacher_token)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        log(f"FAILED {exc}")
        raise
