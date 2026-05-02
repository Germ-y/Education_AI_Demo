from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    external_key: Mapped[str | None] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    region_code: Mapped[str | None] = mapped_column(String)

    users = relationship("User", back_populates="organization")
    students = relationship("Student", back_populates="organization")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    email: Mapped[str | None] = mapped_column(String, unique=True)
    display_name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    password_hash: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="active")

    organization = relationship("Organization", back_populates="users")


class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    external_key: Mapped[str | None] = mapped_column(String, unique=True)
    display_name: Mapped[str] = mapped_column(String)
    grade: Mapped[str] = mapped_column(String)
    school_code: Mapped[str | None] = mapped_column(String, index=True)
    student_type: Mapped[str] = mapped_column(String, index=True)
    primary_need: Mapped[str] = mapped_column(String)
    profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String, default="active")

    organization = relationship("Organization", back_populates="students")


class MissionContent(Base, TimestampMixin):
    __tablename__ = "mission_contents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(String, index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    content_type: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    session_goal: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, index=True)
    total_steps: Mapped[int] = mapped_column(Integer, default=4)
    brief_json: Mapped[dict] = mapped_column(JSON, default=dict)
    teacher_review_summary: Mapped[str | None] = mapped_column(Text)
    approved_by_user_id: Mapped[str | None] = mapped_column(String)
    approved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))


class ContentStage(Base):
    __tablename__ = "content_stages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    mission_content_id: Mapped[str] = mapped_column(ForeignKey("mission_contents.id"), index=True)
    step: Mapped[int] = mapped_column(Integer)
    stage_role: Mapped[str] = mapped_column(String)
    template_type: Mapped[str] = mapped_column(String)
    student_title: Mapped[str] = mapped_column(String)
    student_instruction: Mapped[str] = mapped_column(Text)
    template_json: Mapped[dict] = mapped_column(JSON, default=dict)
    realtime_spec_json: Mapped[dict | None] = mapped_column(JSON)
    sort_order: Mapped[int] = mapped_column(Integer)


class ContentAsset(Base, TimestampMixin):
    __tablename__ = "content_assets"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    mission_content_id: Mapped[str] = mapped_column(ForeignKey("mission_contents.id"), index=True)
    stage_id: Mapped[str | None] = mapped_column(String)
    asset_role: Mapped[str] = mapped_column(String, index=True)
    asset_type: Mapped[str] = mapped_column(String)
    provider: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    prompt_json: Mapped[dict | None] = mapped_column(JSON)
    storage_url: Mapped[str] = mapped_column(String)
    preview_url: Mapped[str | None] = mapped_column(String)
    qa_status: Mapped[str] = mapped_column(String)
    approval_status: Mapped[str] = mapped_column(String)


class ContentAttempt(Base):
    __tablename__ = "content_attempts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    mission_content_id: Mapped[str] = mapped_column(ForeignKey("mission_contents.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="in_progress")
    current_step: Mapped[int] = mapped_column(Integer, default=1)
    started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    score_json: Mapped[dict | None] = mapped_column(JSON)


class RealtimePracticeSession(Base):
    __tablename__ = "realtime_practice_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("content_attempts.id"), index=True)
    mission_content_id: Mapped[str] = mapped_column(ForeignKey("mission_contents.id"))
    stage_id: Mapped[str] = mapped_column(String)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    provider: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="created")
    spec_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_sec: Mapped[int] = mapped_column(Integer, default=0)
    rubric_result_json: Mapped[dict | None] = mapped_column(JSON)
    transcript_summary: Mapped[str | None] = mapped_column(Text)


class PublicDataSource(Base):
    __tablename__ = "public_data_sources"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source_code: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    base_url: Mapped[str | None] = mapped_column(String)
    auth_type: Mapped[str] = mapped_column(String)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ReviewSummary(Base):
    __tablename__ = "review_summaries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("content_attempts.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    completion_rate: Mapped[float] = mapped_column(Numeric)
    accuracy_rate: Mapped[float] = mapped_column(Numeric)
    short_summary: Mapped[str] = mapped_column(Text)
    wrong_pattern_json: Mapped[dict] = mapped_column(JSON, default=dict)
    realtime_result_json: Mapped[dict] = mapped_column(JSON, default=dict)
