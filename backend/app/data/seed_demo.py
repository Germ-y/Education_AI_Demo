import json

from app.core.config import get_settings
from app.data.demo_data import create_demo_database
from app.db.session import create_schema, get_session_maker
from app.repositories.demo_repository import DemoRepository


def main() -> None:
    db = create_demo_database(include_students=False, include_mission_contents=False)
    create_schema()
    repository = DemoRepository(get_session_maker())
    repository.replace_database(db)
    loaded = repository.load_database()
    settings = get_settings()
    print(
        json.dumps(
            {
                "databaseUrl": _safe_database_label(settings.database_url),
                "organizations": len(loaded.organizations),
                "users": len(loaded.users),
                "students": len(loaded.students),
                "schools": len(loaded.schools),
                "schoolCalendarEvents": len(loaded.school_calendar_events),
                "schoolTimetableSlots": len(loaded.school_timetable_slots),
                "supportCases": len(loaded.support_cases),
                "memoryCards": len(loaded.memory_cards),
                "missionContents": len(loaded.mission_contents),
                "publicDataSources": len(loaded.public_data_sources),
                "studentSupportIntakeSources": len(loaded.student_support_intake_sources),
                "studentSupportProfiles": len(loaded.student_support_profiles),
                "studentContextBriefs": len(loaded.student_context_briefs),
                "teacherReportDrafts": len(loaded.teacher_report_drafts),
                "teacherReports": len(loaded.teacher_reports),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _safe_database_label(database_url: str) -> str:
    if database_url.startswith("sqlite"):
        return database_url
    scheme, _, rest = database_url.partition("://")
    host = rest.rsplit("@", maxsplit=1)[-1].split("/", maxsplit=1)[0]
    return f"{scheme}://{host}"


if __name__ == "__main__":
    main()
