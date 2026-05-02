import json

from app.data.demo_data import create_demo_database


def main() -> None:
    db = create_demo_database()
    print(
        json.dumps(
            {
                "organizations": len(db.organizations),
                "users": len(db.users),
                "students": len(db.students),
                "supportCases": len(db.support_cases),
                "memoryCards": len(db.memory_cards),
                "missionContents": len(db.mission_contents),
                "publicDataSources": len(db.public_data_sources),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
