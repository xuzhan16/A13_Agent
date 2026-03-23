from pydantic import BaseModel, Field


class QuestionAnswer(BaseModel):
    question: str
    answer: str


class EvidenceItem(BaseModel):
    source: str
    excerpt: str


class DimensionScore(BaseModel):
    name: str
    score: float
    weight: float
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    evidences: list[EvidenceItem] = Field(default_factory=list)
