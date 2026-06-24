from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    status: str
    chunks: int
    error: str | None = None


class UploadResult(BaseModel):
    uploaded: list[DocumentOut]


class IngestStatus(BaseModel):
    status: str
    documents: list[DocumentOut]


class CountRequest(BaseModel):
    count: int = Field(ge=1)  # capped in practice by number of source chunks


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    question: str
    options: list[str] | None = None
    answer: str | None = None
    explanation: str | None = None
    rubric: list[str] | None = None
    source_file: str | None = None
    source_page: int | None = None


class TestRequest(BaseModel):
    mcq_count: int = Field(ge=0)
    descriptive_count: int = Field(ge=0)


class TestQuestionOut(BaseModel):
    """Question as shown during a test — no answer/explanation/rubric."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    question: str
    options: list[str] | None = None
    source_file: str | None = None
    source_page: int | None = None


class TestView(BaseModel):
    id: int
    questions: list[TestQuestionOut]


class AttemptRequest(BaseModel):
    answers: dict[str, str | None] = {}
