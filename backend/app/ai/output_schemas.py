from __future__ import annotations

from copy import deepcopy
from typing import Any


def output_json_schema(name: str) -> dict[str, Any]:
    schema = _OUTPUT_JSON_SCHEMAS.get(name)
    if schema is None:
        raise KeyError(f"Unknown output schema: {name}")
    return deepcopy(schema)


def _string_array() -> dict[str, Any]:
    return {"type": "array", "items": {"type": "string"}}


def _object_schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or list(properties.keys()),
        "additionalProperties": False,
    }


_SCENARIO_SPINE_SCHEMA = _object_schema(
    {
        "scenarioTitle": {"type": "string"},
        "anchorSituation": {"type": "string"},
        "targetSkill": {"type": "string"},
        "keyEvidence": {"type": "string"},
        "studentAction": {"type": "string"},
        "emotionalTone": {"type": "string"},
        "commonMistakeOrImpulse": {"type": "string"},
        "whyThisMatters": {"type": "string"},
        "studentLikelyImpulseOrMisconception": {"type": "string"},
        "stage2FirstSuccess": {"type": "string"},
        "stage3Transfer": {"type": "string"},
        "stage4Reuse": {"type": "string"},
    }
)

_STAGE_VISUAL_SPEC_SCHEMA = _object_schema(
    {
        "assetRole": {"type": "string", "enum": ["hero", "stage_1", "stage_2", "stage_3", "stage_4_realtime"]},
        "step": {"type": "integer"},
        "visualPurpose": {"type": "string"},
        "sceneSummary": {"type": "string"},
        "primaryEvidenceObject": {"type": "string"},
        "evidenceLocation": {"type": "string"},
        "mustShow": _string_array(),
        "allowedSceneText": _string_array(),
        "doNotRenderText": _string_array(),
        "composition": {"type": "string"},
    }
)

_ASSET_BUNDLE_SCHEMA = _object_schema(
    {
        "imageAssetId": {"type": "string"},
        "audioAssetId": {"type": "string"},
    }
)

_CHOICE_ITEM_SCHEMA = _object_schema(
    {
        "id": {"type": "string"},
        "text": {"type": "string"},
    }
)


def _scene_text_fields() -> dict[str, Any]:
    return {
        "sourceTextLines": _string_array(),
        "sceneTextLines": _string_array(),
    }


_INTRO_TEMPLATE_SCHEMA = _object_schema(
    {
        "imageAssetId": {"type": "string"},
        "audioAssetId": {"type": "string"},
        "assetBundle": _ASSET_BUNDLE_SCHEMA,
        "storyText": {"type": "string"},
        "missionText": {"type": "string"},
        **_scene_text_fields(),
    }
)

_CHOICE_TEMPLATE_SCHEMA = _object_schema(
    {
        "imageAssetId": {"type": "string"},
        "audioAssetId": {"type": "string"},
        "assetBundle": _ASSET_BUNDLE_SCHEMA,
        "question": {"type": "string"},
        "choices": {"type": "array", "items": _CHOICE_ITEM_SCHEMA},
        "answer": {"type": "string"},
        "correctFeedback": {"type": "string"},
        "wrongFeedback": {"type": "string"},
        **_scene_text_fields(),
    }
)

_CARD_MATCH_TEMPLATE_SCHEMA = _object_schema(
    {
        "imageAssetId": {"type": "string"},
        "audioAssetId": {"type": "string"},
        "assetBundle": _ASSET_BUNDLE_SCHEMA,
        "question": {"type": "string"},
        "leftCards": {"type": "array", "items": _CHOICE_ITEM_SCHEMA},
        "rightCards": {"type": "array", "items": _CHOICE_ITEM_SCHEMA},
        "matches": _object_schema(
            {
                "left_1": {"type": "string"},
                "left_2": {"type": "string"},
            }
        ),
        "correctFeedback": {"type": "string"},
        "wrongFeedback": {"type": "string"},
        **_scene_text_fields(),
    }
)

_SEQUENCE_ORDERING_TEMPLATE_SCHEMA = _object_schema(
    {
        "imageAssetId": {"type": "string"},
        "audioAssetId": {"type": "string"},
        "assetBundle": _ASSET_BUNDLE_SCHEMA,
        "question": {"type": "string"},
        "cards": {"type": "array", "items": _CHOICE_ITEM_SCHEMA},
        "answerOrder": _string_array(),
        "correctFeedback": {"type": "string"},
        "wrongFeedback": {"type": "string"},
        **_scene_text_fields(),
    }
)

_BLANK_FILL_TEMPLATE_SCHEMA = _object_schema(
    {
        "imageAssetId": {"type": "string"},
        "audioAssetId": {"type": "string"},
        "assetBundle": _ASSET_BUNDLE_SCHEMA,
        "question": {"type": "string"},
        "sentence": {"type": "string"},
        "tiles": _string_array(),
        "acceptedAnswers": {
            "type": "array",
            "items": _object_schema({"answer": {"type": "string"}}),
        },
        "correctFeedback": {"type": "string"},
        "wrongFeedback": {"type": "string"},
        **_scene_text_fields(),
    }
)

_WRONG_EXPLANATION_FIX_TEMPLATE_SCHEMA = _object_schema(
    {
        "imageAssetId": {"type": "string"},
        "audioAssetId": {"type": "string"},
        "assetBundle": _ASSET_BUNDLE_SCHEMA,
        "question": {"type": "string"},
        "wrongLine": {"type": "string"},
        "choices": {"type": "array", "items": _CHOICE_ITEM_SCHEMA},
        "answer": {"type": "string"},
        "fixedLine": {"type": "string"},
        "correctFeedback": {"type": "string"},
        "wrongFeedback": {"type": "string"},
        **_scene_text_fields(),
    }
)

_PARTITION_PICKER_TEMPLATE_SCHEMA = _object_schema(
    {
        "imageAssetId": {"type": "string"},
        "audioAssetId": {"type": "string"},
        "assetBundle": _ASSET_BUNDLE_SCHEMA,
        "question": {"type": "string"},
        "wholeLabel": {"type": "string"},
        "partLabel": {"type": "string"},
        "choices": {"type": "array", "items": _CHOICE_ITEM_SCHEMA},
        "answer": {"type": "string"},
        "correctFeedback": {"type": "string"},
        "wrongFeedback": {"type": "string"},
        **_scene_text_fields(),
    }
)

_REALTIME_TEMPLATE_SCHEMA = _object_schema(
    {
        "imageAssetId": {"type": "string"},
        "audioAssetId": {"type": "string"},
        "assetBundle": _ASSET_BUNDLE_SCHEMA,
        "situationText": {"type": "string"},
        "practicePrompt": {"type": "string"},
        **_scene_text_fields(),
    }
)

_TEMPLATE_JSON_SCHEMA = {
    "anyOf": [
        _INTRO_TEMPLATE_SCHEMA,
        _CHOICE_TEMPLATE_SCHEMA,
        _CARD_MATCH_TEMPLATE_SCHEMA,
        _SEQUENCE_ORDERING_TEMPLATE_SCHEMA,
        _BLANK_FILL_TEMPLATE_SCHEMA,
        _WRONG_EXPLANATION_FIX_TEMPLATE_SCHEMA,
        _PARTITION_PICKER_TEMPLATE_SCHEMA,
        _REALTIME_TEMPLATE_SCHEMA,
    ],
}

_IMAGE_PROMPT_JSON_SCHEMA = _object_schema(
    {
        "prompt": {"type": "string"},
        "textRenderingPolicy": {"type": "string"},
        "ocrPolicy": {"type": "string"},
        "ocrRequired": {"type": "boolean"},
        "sceneTextLines": _string_array(),
    }
)

_PROMPT_JSON_SCHEMA = {"anyOf": [_IMAGE_PROMPT_JSON_SCHEMA, {"type": "null"}]}

_REALTIME_SPEC_SCHEMA = _object_schema(
    {
        "id": {"type": "string"},
        "stageId": {"type": "string"},
        "templateType": {"type": "string", "enum": ["realtime_roleplay", "realtime_teach_back"]},
        "imageAssetId": {"type": "string"},
        "mode": {"type": "string", "enum": ["voice_or_text", "voice", "text"]},
        "practiceTitle": {"type": "string"},
        "situationText": {"type": "string"},
        "aiRole": {"type": "string"},
        "openingLine": {"type": "string"},
        "studentGoal": {"type": "string"},
        "rubric": {
            "type": "array",
            "items": _object_schema(
                {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "required": {"type": "boolean"},
                }
            ),
        },
        "allowedFeedback": _string_array(),
        "forbidden": _string_array(),
        "maxTurns": {"type": "integer"},
        "maxDurationSec": {"type": "integer"},
        "postPracticeReflection": _string_array(),
    }
)

_CONTENT_STAGE_SCHEMA = _object_schema(
    {
        "id": {"type": "string"},
        "missionContentId": {"type": "string"},
        "step": {"type": "integer"},
        "stageRole": {
            "type": "string",
            "enum": [
                "scenario_intro",
                "clue_identification",
                "action_selection",
                "concept_intro",
                "basic_problem",
                "applied_problem",
                "realtime_practice",
            ],
        },
        "templateType": {
            "type": "string",
            "enum": [
                "scenario_intro",
                "scene_observation",
                "highlight_clue",
                "card_match",
                "action_choice",
                "sequence_ordering",
                "decision_card",
                "image_quiz",
                "concept_intro",
                "scene_question",
                "clue_question",
                "blank_fill",
                "partition_picker",
                "applied_question",
                "mini_simulation",
                "explanation_choice",
                "wrong_explanation_fix",
                "realtime_roleplay",
                "realtime_teach_back",
            ],
        },
        "studentTitle": {"type": "string"},
        "studentInstruction": {"type": "string"},
        "sortOrder": {"type": "integer"},
        "templateJson": _TEMPLATE_JSON_SCHEMA,
        "realtimeSpec": {"anyOf": [_REALTIME_SPEC_SCHEMA, {"type": "null"}]},
    }
)

_CONTENT_ASSET_SCHEMA = _object_schema(
    {
        "id": {"type": "string"},
        "missionContentId": {"type": "string"},
        "stageId": {"type": ["string", "null"]},
        "assetRole": {"type": "string", "enum": ["hero", "stage_1", "stage_2", "stage_3", "stage_4_realtime"]},
        "assetType": {"type": "string", "enum": ["image", "audio"]},
        "provider": {"type": "string"},
        "model": {"type": "string"},
        "promptJson": _PROMPT_JSON_SCHEMA,
        "sourceText": {"type": ["string", "null"]},
        "storageUrl": {"type": "string"},
        "previewUrl": {"type": ["string", "null"]},
        "qaStatus": {"type": "string", "enum": ["pending", "passed", "failed"]},
        "approvalStatus": {"type": "string", "enum": ["pending", "approved", "rejected"]},
    }
)

_MISSION_CONTENT_SCHEMA = _object_schema(
    {
        "id": {"type": "string"},
        "studentId": {"type": "string"},
        "caseId": {"type": "string"},
        "contentType": {"type": "string", "enum": ["life_support", "learning_focus"]},
        "title": {"type": "string"},
        "sessionGoal": {"type": "string"},
        "status": {"type": "string", "enum": ["teacher_review"]},
        "totalSteps": {"type": "integer", "enum": [4]},
        "briefJson": _object_schema(
            {
                "orchestratorPlanVersion": {"type": "string"},
                "targetSkill": {"type": "string"},
                "strategy": {"type": "string"},
                "teacherReviewFocus": _string_array(),
                "scenarioSpine": _SCENARIO_SPINE_SCHEMA,
                "stageVisualSpecs": {"type": "array", "items": _STAGE_VISUAL_SPEC_SCHEMA},
            }
        ),
        "stages": {"type": "array", "items": _CONTENT_STAGE_SCHEMA},
        "assets": {"type": "array", "items": _CONTENT_ASSET_SCHEMA},
        "teacherReviewSummary": {"type": "string"},
    }
)

_ORCHESTRATOR_STAGE_SCHEMA = _object_schema(
    {
        "step": {"type": "integer"},
        "stageRole": {"type": "string"},
        "templateType": {"type": "string"},
        "studentTitle": {"type": "string"},
        "purpose": {"type": "string"},
        "templateRationale": {"type": "string"},
    }
)

_ORCHESTRATOR_PLAN_SCHEMA = _object_schema(
    {
        "planVersion": {"type": "string"},
        "studentId": {"type": "string"},
        "caseId": {"type": "string"},
        "contentType": {"type": "string", "enum": ["life_support", "learning_focus"]},
        "sessionGoal": {"type": "string"},
        "targetSkill": {"type": "string"},
        "scenarioSpine": _SCENARIO_SPINE_SCHEMA,
        "stagePlan": {"type": "array", "items": _ORCHESTRATOR_STAGE_SCHEMA},
        "stageVisualSpecs": {"type": "array", "items": _STAGE_VISUAL_SPEC_SCHEMA},
        "imagePackageIntent": {
            "type": "array",
            "items": _object_schema(
                {
                    "assetRole": {"type": "string", "enum": ["hero", "stage_1", "stage_2", "stage_3", "stage_4_realtime"]},
                    "scenePurpose": {"type": "string"},
                    "mustShow": _string_array(),
                    "learningObject": {"type": "string"},
                    "compositionHint": {"type": "string"},
                    "mustNotShow": _string_array(),
                }
            ),
        },
        "ttsNarrationIntent": {
            "type": "array",
            "items": _object_schema(
                {
                    "assetRole": {"type": "string", "enum": ["hero", "stage_1", "stage_2", "stage_3", "stage_4_realtime"]},
                    "voicePurpose": {"type": "string"},
                    "tone": {"type": "string", "enum": ["calm", "bright", "reassuring"]},
                }
            ),
        },
        "teacherReviewFocus": _string_array(),
        "safetyNotes": _string_array(),
    }
)

_IMAGE_BRIEF_SCHEMA = _object_schema(
    {
        "promptVersion": {"type": "string"},
        "contentId": {"type": "string"},
        "imageBriefs": {
            "type": "array",
            "items": _object_schema(
                {
                    "assetRole": {"type": "string", "enum": ["hero", "stage_1", "stage_2", "stage_3", "stage_4_realtime"]},
                    "stageId": {"type": ["string", "null"]},
                    "prompt": {"type": "string"},
                    "negativePromptRules": _string_array(),
                    "learningEvidence": _object_schema(
                        {
                            "primaryObject": {"type": "string"},
                            "mustBeReadableOrCountable": _string_array(),
                            "whyItMattersForThisStage": {"type": "string"},
                        }
                    ),
                    "compositionPlan": _object_schema(
                        {
                            "camera": {"type": "string"},
                            "subjectPriority": {"type": "string"},
                            "humanPresence": {"type": "string"},
                        }
                    ),
                    "ocrRequired": {"type": "boolean"},
                    "sceneTextLines": _string_array(),
                    "textRenderingPolicy": {"type": "string"},
                    "qaChecklist": _string_array(),
                }
            ),
        },
    }
)

_TTS_SCRIPT_SCHEMA = _object_schema(
    {
        "scripts": {
            "type": "array",
            "items": _object_schema(
                {
                    "assetRole": {"type": "string", "enum": ["hero", "stage_1", "stage_2", "stage_3", "stage_4_realtime"]},
                    "sourceText": {"type": "string"},
                    "tone": {"type": "string", "enum": ["calm", "bright", "reassuring"]},
                }
            ),
        }
    }
)

_CONTENT_QUALITY_CRITIQUE_SCHEMA = _object_schema(
    {
        "verdict": {"type": "string", "enum": ["pass", "repair"]},
        "issues": _string_array(),
        "repairInstruction": {"type": "string"},
    }
)

_SUPPORT_PROFILE_DRAFT_SCHEMA = _object_schema(
    {
        "profileVersion": {"type": "string", "enum": ["support_profile_v1"]},
        "draftLabel": {"type": "string"},
        "lessonDesignHints": _string_array(),
        "learningResponsePattern": _object_schema(
            {
                "worksWell": _string_array(),
                "canBeHard": _string_array(),
                "choiceCountLimit": {"type": "integer"},
                "readingLoad": {"type": "string", "enum": ["low", "medium", "high"]},
                "explanationStyle": {"type": "string"},
            }
        ),
        "behaviorSupportProfile": _object_schema(
            {
                "priorityBehaviors": _string_array(),
                "functionHypotheses": _string_array(),
                "replacementSkills": _string_array(),
                "recommendedScaffolds": _string_array(),
            }
        ),
        "strengths": _string_array(),
        "supportCautions": _string_array(),
        "source": _object_schema(
            {
                "intakeSourceId": {"type": ["string", "null"]},
                "generatedBy": {"type": "string"},
                "rawRecordPreserved": {"type": "boolean"},
            }
        ),
    }
)

_STUDENT_MEMORY_BRIEF_SCHEMA = _object_schema(
    {
        "briefText": {"type": "string"},
        "readingLoad": {"type": "string", "enum": ["low", "medium", "high"]},
        "choiceCount": {"type": "integer"},
        "recentSuccessPatterns": _string_array(),
        "recentDifficultyPatterns": _string_array(),
        "recommendedScaffolds": _string_array(),
        "avoidTopicRegression": _string_array(),
        "sourceWatermark": {"type": "string"},
    }
)

_OUTPUT_JSON_SCHEMAS: dict[str, dict[str, Any]] = {
    "OrchestratorPlanV1": _ORCHESTRATOR_PLAN_SCHEMA,
    "MissionContentPackageV1": _MISSION_CONTENT_SCHEMA,
    "ImageBriefPackageV1": _IMAGE_BRIEF_SCHEMA,
    "TtsScriptPackageV1": _TTS_SCRIPT_SCHEMA,
    "ContentQualityCritiqueV1": _CONTENT_QUALITY_CRITIQUE_SCHEMA,
    "SupportProfileDraftV1": _SUPPORT_PROFILE_DRAFT_SCHEMA,
    "StudentMemoryBriefV1": _STUDENT_MEMORY_BRIEF_SCHEMA,
}
