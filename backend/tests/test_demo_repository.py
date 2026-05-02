from sqlalchemy.orm import sessionmaker

from app.data.demo_data import create_demo_database
from app.db.session import create_database_engine, create_schema
from app.repositories.demo_repository import DemoRepository


def test_repository_round_trips_seed_database() -> None:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    repository = DemoRepository(sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True))

    repository.replace_database(create_demo_database())
    loaded = repository.load_database()

    assert len(loaded.users) == 1
    assert len(loaded.students) == 3
    assert len(loaded.schools) == 3
    assert len(loaded.mission_contents) == 3
    assert len(loaded.review_summaries) == 2
    assert loaded.review_summaries[0].short_summary
    assert "Completed" not in loaded.review_summaries[0].short_summary
    assert loaded.mission_contents[0].total_steps == 4
    assert {stage.step for stage in loaded.mission_contents[0].stages} == {1, 2, 3, 4}
