from typing import Any

from pydantic import BaseModel, Field


class QuestionAnswer(BaseModel):
    question: str
    answer: str
    question_id: str = ''


class EvidenceItem(BaseModel):
    evidence_id: str = ''
    source: str = ''
    source_type: str = ''
    source_ref: str = ''
    excerpt: str
    normalized_value: Any = ''
    confidence: float = 1.0
    extract_rule: str = ''
    tags: list[str] = Field(default_factory=list)


class ScoreDeduction(BaseModel):
    reason: str
    delta: float


class IndicatorScore(BaseModel):
    indicator_code: str
    indicator_name: str
    weight_in_dimension: float
    raw_value: Any = None
    score: float
    weighted_score: float
    rule_id: str
    formula: str = ''
    evidence_refs: list[str] = Field(default_factory=list)
    deductions: list[ScoreDeduction] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class DimensionScore(BaseModel):
    name: str
    dimension_code: str = ''
    score: float
    weight: float
    weighted_score: float = 0
    formula: str = ''
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    evidences: list[EvidenceItem] = Field(default_factory=list)
    indicators: list[IndicatorScore] = Field(default_factory=list)
