"""Request / response models for the API (pydantic v2)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ClientInfo(BaseModel):
    name: str | None = None
    age: int | None = Field(default=None, ge=0, le=130)
    sex: str | None = None


class DiagnoseRequest(BaseModel):
    """The frontend submits the list of present finding-codes the client selected."""
    codes: list[str] = Field(default_factory=list)
    client: ClientInfo | None = None
    case_id: str = "case"


class QuestionOption(BaseModel):
    code: str
    label: str


class QuestionSection(BaseModel):
    key: str
    title: str
    hint: str
    input: str  # "checklist"
    options: list[QuestionOption]


class QuestionsResponse(BaseModel):
    sections: list[QuestionSection]
    total_codes: int
