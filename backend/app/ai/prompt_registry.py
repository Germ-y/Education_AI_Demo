from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"


@dataclass(frozen=True)
class PromptSpec:
    key: str
    version: str
    file_name: str
    output_schema_name: str


PROMPT_SPECS: dict[str, PromptSpec] = {
    "orchestrator_plan": PromptSpec(
        key="orchestrator_plan",
        version="orchestrator_plan_v1",
        file_name="orchestrator_plan_v1.md",
        output_schema_name="OrchestratorPlanV1",
    ),
    "mission_content_package": PromptSpec(
        key="mission_content_package",
        version="mission_content_package_v1",
        file_name="mission_content_package_v1.md",
        output_schema_name="MissionContentPackageV1",
    ),
    "image_brief": PromptSpec(
        key="image_brief",
        version="image_brief_v1",
        file_name="image_brief_v1.md",
        output_schema_name="ImageBriefPackageV1",
    ),
    "content_quality_critique": PromptSpec(
        key="content_quality_critique",
        version="content_quality_critique_v1",
        file_name="content_quality_critique_v1.md",
        output_schema_name="ContentQualityCritiqueV1",
    ),
    "tts_script": PromptSpec(
        key="tts_script",
        version="tts_script_v1",
        file_name="tts_script_v1.md",
        output_schema_name="TtsScriptPackageV1",
    ),
    "teacher_report_draft": PromptSpec(
        key="teacher_report_draft",
        version="teacher_report_draft_v1",
        file_name="teacher_report_draft_v1.md",
        output_schema_name="",
    ),
}


@lru_cache
def load_prompt(key: str) -> str:
    spec = PROMPT_SPECS[key]
    return (PROMPT_DIR / spec.file_name).read_text(encoding="utf-8")


def list_prompt_specs() -> list[PromptSpec]:
    return list(PROMPT_SPECS.values())
