from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "eduyj_demo.db"
ASSET_ROOT = Path(__file__).resolve().parents[1] / "generated" / "assets"


REVIEW_CONTENTS = {
    "content_showcase_learning-clock_record": {
        "title": "학교 시간표에서 시작 시간 찾기",
        "goal": "학교 시간표와 아날로그 시계를 함께 보고 활동 시작 시간을 찾는 검토용 수업",
        "summary": "현재용 시계 말하기 자료와 다르게, 학교 시간표 상황에서 시작 시간을 고르는 검토용 자료입니다.",
        "object": "학교 시간표와 벽시계",
        "place": "교실 앞 시간표 게시판",
        "skill": "시간표의 활동 이름을 보고 시작 시간을 시계에서 확인하기",
        "correct": "10시 30분",
        "other1": "9시 30분",
        "other2": "11시 30분",
        "scene": "한국 초등학교 교실 앞 시간표 게시판과 둥근 벽시계가 보이는 밝은 장면. 학생 한 명이 시간표를 손가락으로 짚고 있고, 선생님은 옆에서 차분히 기다린다. 문제 문장이나 선택지는 넣지 않는다.",
        "audio": "시간표에서 활동 이름을 먼저 보고, 벽시계의 긴 바늘과 짧은 바늘을 차례로 확인해요.",
        "realtime": "선생님에게 활동이 몇 시 몇 분에 시작하는지 짧게 말해보기",
    },
    "content_showcase_learning-fraction_record": {
        "title": "색칠 막대로 분수 만들기",
        "goal": "피자나 간식 나누기와 다르게, 같은 길이 막대에서 색칠된 부분을 보고 분수를 말하는 검토용 수업",
        "summary": "현재용 간식 나누기 자료와 다르게, 색칠 막대 모델로 전체-부분 관계를 검토하는 자료입니다.",
        "object": "네 칸으로 나뉜 색칠 막대",
        "place": "수학 활동 책상",
        "skill": "전체가 같은 크기 네 칸일 때 색칠된 칸을 분수로 말하기",
        "correct": "2/4",
        "other1": "1/4",
        "other2": "3/4",
        "scene": "한국 중학교 수학 활동 책상 위에 같은 크기 네 칸으로 나뉜 직사각형 막대 카드가 놓여 있고, 앞의 두 칸만 또렷한 초록색으로 색칠되어 있다. 학생은 카드를 보고 전체와 부분을 비교한다. 문제 문장이나 정답 텍스트는 넣지 않는다.",
        "audio": "전체가 몇 칸인지 먼저 세고, 색칠된 칸이 몇 칸인지 천천히 확인해요.",
        "realtime": "전체 네 칸 중 색칠된 두 칸을 분수로 설명해보기",
    },
    "content_showcase_life-bus_record": {
        "title": "보건실 위치 물어보기",
        "goal": "버스 정류장 도움 요청과 다르게, 학교 안에서 보건실 위치를 물어보는 검토용 생활 의사소통 수업",
        "summary": "현재용 정류장 자료와 다르게, 학교 복도에서 필요한 장소를 묻는 검토용 자료입니다.",
        "object": "학교 복도와 보건실 안내 표지",
        "place": "학교 복도",
        "skill": "낯선 복도에서 필요한 장소를 찾기 위해 짧게 도움 요청하기",
        "correct": "선생님, 보건실이 어디인지 알려 주세요.",
        "other1": "저는 그냥 여기 있을게요.",
        "other2": "아무 말도 하지 않을래요.",
        "scene": "한국 초등학교 복도에서 학생 한 명이 보건실 방향을 찾고 있고, 교직원이 가까운 거리에서 친절하게 바라본다. 벽에는 단순한 방향 표시 아이콘만 있고 긴 글자는 없다. 안전하고 차분한 생활 교육 일러스트 장면.",
        "audio": "필요한 장소를 찾기 어려울 때는 가까운 어른에게 짧게 물어볼 수 있어요.",
        "realtime": "교직원에게 보건실 위치를 알려 달라고 말해보기",
    },
}


def asset_prompt(content_id: str, asset_role: str, scene: str) -> str:
    if asset_role == "hero":
        detail = scene
    elif asset_role == "stage_1":
        detail = f"{scene} 학생이 전체 상황을 먼저 살피는 도입 장면."
    elif asset_role == "stage_2":
        detail = f"{scene} 중요한 단서가 되는 물건이나 위치가 화면 중심에 보이는 장면."
    elif asset_role == "stage_3":
        detail = f"{scene} 학생이 두 가지 행동 중 적절한 행동을 생각하는 장면."
    else:
        detail = f"{scene} 학생이 짧은 문장으로 직접 말하기를 연습하는 장면."
    return json.dumps(
        {
            "prompt": f"{detail} 교육용 디지털 콘텐츠용 선명한 일러스트. 화면 안에 문제 문장, 정답, 선택지, 긴 글자를 넣지 않는다. content id: {content_id}.",
            "visualRole": asset_role,
            "textRenderingPolicy": "scene_only_no_problem_text",
            "ocrPolicy": "scene_only_no_problem_text",
            "avoid": ["문제 문장", "정답 표시", "선택지", "힌트 텍스트", "과도한 표정", "위험한 장면"],
        },
        ensure_ascii=False,
    )


def stage_template(content: dict[str, str], step: int, image_asset_id: str, audio_asset_id: str) -> dict:
    if step == 1:
        return {
            "question": f"{content['object']}를 보고 오늘 연습할 상황을 살펴봐요.",
            "missionText": content["skill"],
            "imageAssetId": image_asset_id,
            "audioAssetId": audio_asset_id,
        }
    return {
        "question": f"{content['place']} 장면에서 알맞은 말을 골라요.",
        "choices": [
            {"id": "a", "text": content["correct"]},
            {"id": "b", "text": content["other1"]},
            {"id": "c", "text": content["other2"]},
        ],
        "answer": "a",
        "correctFeedback": "좋아요. 중요한 단서를 잘 확인했어요.",
        "wrongFeedback": "괜찮아요. 그림 단서를 다시 천천히 살펴봐요.",
        "imageAssetId": image_asset_id,
        "audioAssetId": audio_asset_id,
    }


def realtime_spec(content: dict[str, str], stage_id: str, image_asset_id: str) -> dict:
    return {
        "id": f"rt_spec_{stage_id}",
        "stageId": stage_id,
        "templateType": "realtime_roleplay",
        "imageAssetId": image_asset_id,
        "mode": "voice_or_text",
        "practiceTitle": "짧게 말해보기",
        "situationText": f"{content['place']}에서 {content['skill']} 연습을 합니다.",
        "aiRole": "친절한 연습 파트너",
        "openingLine": "천천히 한 문장으로 말해볼까요?",
        "studentGoal": content["realtime"],
        "rubric": [
            {"id": "try", "label": "말하기를 시도함", "required": True},
            {"id": "target", "label": "필요한 말을 짧게 표현함", "required": True},
        ],
        "allowedFeedback": ["좋아요.", "천천히 다시 말해봐도 괜찮아요."],
        "forbidden": ["진단명 언급", "개인정보 질문", "정답 강요"],
        "maxTurns": 3,
        "maxDurationSec": 120,
        "postPracticeReflection": ["쉬웠어요", "한 번 더 해볼래요", "도움이 필요해요"],
    }


def main() -> None:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    for content_id, content in REVIEW_CONTENTS.items():
        con.execute(
            """
            update mission_contents
               set title = ?,
                   session_goal = ?,
                   status = 'teacher_review',
                   published_at = null,
                   teacher_review_summary = ?
             where id = ?
            """,
            (content["title"], content["goal"], content["summary"], content_id),
        )

        stages = con.execute(
            "select id, step from content_stages where mission_content_id = ? order by step",
            (content_id,),
        ).fetchall()
        for stage in stages:
            step = stage["step"]
            role = "stage_4_realtime" if step == 4 else f"stage_{step}"
            image_asset_id = f"asset_{content_id}_{role}"
            audio_asset_id = f"asset_{content_id}_{role}_audio"
            template = stage_template(content, step, image_asset_id, audio_asset_id)
            spec = realtime_spec(content, stage["id"], image_asset_id) if step == 4 else None
            con.execute(
                """
                update content_stages
                   set student_title = ?,
                       student_instruction = ?,
                       template_json = ?,
                       realtime_spec_json = ?
                 where id = ?
                """,
                (
                    ["상황 보기", "단서 찾기", "알맞은 말 고르기", "직접 말해보기"][step - 1],
                    content["skill"],
                    json.dumps(template, ensure_ascii=False),
                    None if spec is None else json.dumps(spec, ensure_ascii=False),
                    stage["id"],
                ),
            )

        assets = con.execute(
            "select id, asset_role, asset_type from content_assets where mission_content_id = ?",
            (content_id,),
        ).fetchall()
        for asset in assets:
            if asset["asset_type"] == "image":
                prompt = asset_prompt(content_id, asset["asset_role"], content["scene"])
                source_text = None
            else:
                prompt = None
                source_text = content["audio"]
            con.execute(
                """
                update content_assets
                   set prompt_json = ?,
                       source_text = ?,
                       storage_url = '',
                       preview_url = '',
                       qa_status = 'pending',
                       approval_status = 'pending'
                 where id = ?
                """,
                (prompt, source_text, asset["id"]),
            )

        asset_dir = ASSET_ROOT / content_id
        if asset_dir.exists():
            shutil.rmtree(asset_dir)

    con.commit()
    print(json.dumps({"updatedReviewContents": list(REVIEW_CONTENTS)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
