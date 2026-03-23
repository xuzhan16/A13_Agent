from typing import Optional

from pydantic import BaseModel, Field

from backend.app.schemas.job import MatchResult
from backend.app.schemas.student import StudentIntakeRequest, StudentProfile


class CareerPathStep(BaseModel):
    role: str
    stage: str
    description: str
    unlock_conditions: list[str] = Field(default_factory=list)


class CareerPathOption(BaseModel):
    path_name: str
    path_type: str
    fit_reason: str
    steps: list[CareerPathStep] = Field(default_factory=list)


class ActionPlanItem(BaseModel):
    phase: str
    objective: str
    actions: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)


class FollowUpQuestion(BaseModel):
    question_id: str
    question: str
    reason: str
    priority: int = 1


class PlanningMetadata(BaseModel):
    profile_mode: str = 'rule_based'
    report_mode: str = 'template'
    llm_enabled: bool = False
    knowledge_base_source: str = 'unknown'


class CareerReport(BaseModel):
    title: str
    overview: str
    executive_summary: str = ''
    highlight_points: list[str] = Field(default_factory=list)
    recommended_paths: list[CareerPathOption] = Field(default_factory=list)
    action_plan: list[ActionPlanItem] = Field(default_factory=list)
    report_markdown: str
    generation_mode: str = 'template'


class CareerPlanningRequest(BaseModel):
    intake: StudentIntakeRequest
    preferred_job_family: Optional[str] = None
    top_k_matches: int = 3
    max_follow_up_questions: int = 4


class FollowUpQuestionRequest(BaseModel):
    intake: StudentIntakeRequest
    preferred_job_family: Optional[str] = None
    top_k_matches: int = 3
    max_questions: int = 4


class FollowUpQuestionResponse(BaseModel):
    student_profile: StudentProfile
    candidate_job_families: list[str] = Field(default_factory=list)
    questions: list[FollowUpQuestion] = Field(default_factory=list)
    metadata: PlanningMetadata


class CareerPlanningResponse(BaseModel):
    student_profile: StudentProfile
    match_results: list[MatchResult]
    path_options: list[CareerPathOption]
    report: CareerReport
    follow_up_questions: list[FollowUpQuestion] = Field(default_factory=list)
    metadata: PlanningMetadata
