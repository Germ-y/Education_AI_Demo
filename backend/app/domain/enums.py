from enum import StrEnum


class UserRole(StrEnum):
    CENTER_ADMIN = "center_admin"
    TEACHER = "teacher"
    CONTENT_REVIEWER = "content_reviewer"
    GUARDIAN = "guardian"
    STUDENT = "student"


class StudentType(StrEnum):
    LIFE_SUPPORT = "life_support"
    LEARNING_FOCUS = "learning_focus"


class MissionStatus(StrEnum):
    DRAFT = "draft"
    GENERATING = "generating"
    TEACHER_REVIEW = "teacher_review"
    REVISION_REQUESTED = "revision_requested"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class StageRole(StrEnum):
    SCENARIO_INTRO = "scenario_intro"
    CLUE_IDENTIFICATION = "clue_identification"
    ACTION_SELECTION = "action_selection"
    CONCEPT_INTRO = "concept_intro"
    BASIC_PROBLEM = "basic_problem"
    APPLIED_PROBLEM = "applied_problem"
    REALTIME_PRACTICE = "realtime_practice"


class TemplateType(StrEnum):
    SCENARIO_INTRO = "scenario_intro"
    SCENE_OBSERVATION = "scene_observation"
    HIGHLIGHT_CLUE = "highlight_clue"
    CARD_MATCH = "card_match"
    ACTION_CHOICE = "action_choice"
    SEQUENCE_ORDERING = "sequence_ordering"
    DECISION_CARD = "decision_card"
    IMAGE_QUIZ = "image_quiz"
    CONCEPT_INTRO = "concept_intro"
    SCENE_QUESTION = "scene_question"
    CLUE_QUESTION = "clue_question"
    BLANK_FILL = "blank_fill"
    PARTITION_PICKER = "partition_picker"
    APPLIED_QUESTION = "applied_question"
    MINI_SIMULATION = "mini_simulation"
    EXPLANATION_CHOICE = "explanation_choice"
    WRONG_EXPLANATION_FIX = "wrong_explanation_fix"
    REALTIME_ROLEPLAY = "realtime_roleplay"
    REALTIME_TEACH_BACK = "realtime_teach_back"


class AssetRole(StrEnum):
    HERO = "hero"
    STAGE_1 = "stage_1"
    STAGE_2 = "stage_2"
    STAGE_3 = "stage_3"
    STAGE_4_REALTIME = "stage_4_realtime"


class AssetType(StrEnum):
    IMAGE = "image"
    AUDIO_OPTIONAL = "audio_optional"
