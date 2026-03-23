from typing import Optional

from pydantic import BaseModel, Field

from backend.app.schemas.common import DimensionScore


class JobRequirementProfile(BaseModel):
    job_family: str
    description: str
    preferred_majors: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    bonus_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    certificates: list[str] = Field(default_factory=list)
    practice_requirements: list[str] = Field(default_factory=list)
    vertical_growth_path: list[str] = Field(default_factory=list)
    transfer_paths: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    source_titles: list[str] = Field(default_factory=list)
    sample_count: int = 0
    top_cities: list[str] = Field(default_factory=list)
    top_industries: list[str] = Field(default_factory=list)
    salary_min_monthly: Optional[float] = None
    salary_max_monthly: Optional[float] = None
    evidence_snippets: list[str] = Field(default_factory=list)


class MatchResult(BaseModel):
    job_family: str
    overall_score: float
    summary: str
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    dimension_scores: list[DimensionScore] = Field(default_factory=list)
