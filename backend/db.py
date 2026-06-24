from datetime import datetime, timezone

from sqlalchemy import create_engine, String, Integer, Text, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from . import config

engine = create_engine(
    f"sqlite:///{config.DB_PATH}", connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, default="student")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("user_id", "filename"),)  # unique per user, not globally
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    filename: Mapped[str] = mapped_column(String)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)  # bytes
    # pending / processing / completed / failed / partial
    status: Mapped[str] = mapped_column(String, default="pending")
    chunks: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(  # upload date
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chapter: Mapped[str | None] = mapped_column(String, nullable=True)
    embedding_ref: Mapped[str | None] = mapped_column(String, nullable=True)


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # owner
    type: Mapped[str] = mapped_column(String)  # mcq | descriptive
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)      # mcq: 4 strings
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)        # mcq: correct option
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    rubric: Mapped[list | None] = mapped_column(JSON, nullable=True)       # descriptive: marking points
    source_file: Mapped[str | None] = mapped_column(String, nullable=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Rubric(Base):
    __tablename__ = "rubrics"
    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(Integer)
    scoring_points: Mapped[list | None] = mapped_column(JSON, nullable=True)  # list of points
    max_marks: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Test(Base):
    __tablename__ = "tests"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seq: Mapped[int | None] = mapped_column(Integer, nullable=True)  # per-user test number (1,2,3…)
    question_ids: Mapped[list] = mapped_column(JSON)
    question_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, default="created")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Attempt(Base):
    __tablename__ = "attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    test_id: Mapped[int] = mapped_column(Integer, unique=True)  # one attempt per test (no auth yet)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answers: Mapped[dict] = mapped_column(JSON, default=dict)   # {question_id: answer}
    submitted: Mapped[bool] = mapped_column(default=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(  # submitted date
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Evaluation(Base):
    __tablename__ = "evaluations"
    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(Integer)
    per_question_score: Mapped[list | None] = mapped_column(JSON, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_score: Mapped[int | None] = mapped_column(Integer, nullable=True)


def init_db():
    Base.metadata.create_all(engine)
    # ponytail: tiny in-place migration for the per-user test number, so existing data survives
    with engine.begin() as conn:
        cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(tests)").fetchall()]
        if "seq" not in cols:
            conn.exec_driver_sql("ALTER TABLE tests ADD COLUMN seq INTEGER")
            counts = {}
            for tid, uid in conn.exec_driver_sql("SELECT id, user_id FROM tests ORDER BY id").fetchall():
                counts[uid] = counts.get(uid, 0) + 1
                conn.exec_driver_sql("UPDATE tests SET seq = ? WHERE id = ?", (counts[uid], tid))
        ucols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()]
        if "password_hash" not in ucols:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN password_hash VARCHAR")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
