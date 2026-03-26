from typing import Optional

from pydantic import BaseModel, Field

from backend.app.schemas.common import EvidenceItem, QuestionAnswer, SoftSkillAssessment


class StudentBasicInfo(BaseModel):
    name: str = ''
    school: str = ''
    major: str = ''
    degree: str = ''
    graduation_year: Optional[int] = None


class CareerPreference(BaseModel):
    target_roles: list[str] = Field(default_factory=list)
    target_cities: list[str] = Field(default_factory=list)
    desired_industries: list[str] = Field(default_factory=list)
    prefer_stability: bool = False
    prefer_innovation: bool = True


class StudentIntakeRequest(BaseModel):
    basic_info: StudentBasicInfo
    preference: CareerPreference = Field(default_factory=CareerPreference)
    resume_text: str = ''
    self_description: str = ''
    manual_skills: list[str] = Field(default_factory=list)
    project_experiences: list[str] = Field(default_factory=list)
    internship_experiences: list[str] = Field(default_factory=list)
    campus_experiences: list[str] = Field(default_factory=list)
    certificates: list[str] = Field(default_factory=list)
    follow_up_answers: list[QuestionAnswer] = Field(default_factory=list)


class StudentProfile(BaseModel):
    basic_info: StudentBasicInfo
    preference: CareerPreference
    hard_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    soft_skill_assessments: list[SoftSkillAssessment] = Field(default_factory=list)
    certificates: list[str] = Field(default_factory=list)
    inferred_strengths: list[str] = Field(default_factory=list)
    inferred_gaps: list[str] = Field(default_factory=list)
    missing_dimensions: list[str] = Field(default_factory=list)
    project_count: int = 0
    internship_count: int = 0
    campus_count: int = 0
    completeness_score: float = 0
    competitiveness_score: float = 0
    evidences: list[EvidenceItem] = Field(default_factory=list)
    profile_source: str = 'rule_based'
    summary: str = ''
