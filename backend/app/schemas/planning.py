from typing import Any, Optional

from pydantic import BaseModel, Field

from backend.app.schemas.job import MatchResult
from backend.app.schemas.student import StudentIntakeRequest, StudentProfile


class CareerPathStep(BaseModel):
    role: str
    stage: str
    description: str
    unlock_conditions: list[str] = Field(default_factory=list)
    step_type: str = ''
    success_rate: float = 0
    time_cost: str = ''
    required_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class CareerPathOption(BaseModel):
    path_name: str
    path_type: str
    fit_reason: str
    steps: list[CareerPathStep] = Field(default_factory=list)
    target_role: str = ''
    path_jobs: list[str] = Field(default_factory=list)
    readiness_score: float = 0
    estimated_success_rate: float = 0
    estimated_time_cost: str = ''
    missing_skills: list[str] = Field(default_factory=list)
    evidence_sources: list[str] = Field(default_factory=list)
    related_jobs: list[str] = Field(default_factory=list)
    common_entry_roles: list[str] = Field(default_factory=list)


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


class TrendMetric(BaseModel):
    metric_code: str
    metric_name: str
    value: Any = None
    display_value: str = ''
    score: float = 0
    weight: float = 0
    formula: str = ''


class JobHeatInsight(BaseModel):
    job_family: str
    heat_score: float
    heat_level: str
    summary: str = ''
    metrics: list[TrendMetric] = Field(default_factory=list)


class SkillTrendInsight(BaseModel):
    skill_name: str
    category: str = 'missing'
    heat_score: float
    heat_level: str
    summary: str = ''
    suggestion: str = ''
    metrics: list[TrendMetric] = Field(default_factory=list)


class IndustryShiftInsight(BaseModel):
    topic: str
    impact_level: str
    summary: str
    opportunities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class IndustryTrendAnalysis(BaseModel):
    snapshot_version: str
    updated_at: str
    role_heat: list[JobHeatInsight] = Field(default_factory=list)
    missing_skill_trends: list[SkillTrendInsight] = Field(default_factory=list)
    industry_shifts: list[IndustryShiftInsight] = Field(default_factory=list)
    personalized_advice: list[str] = Field(default_factory=list)


class TransferPathEdge(BaseModel):
    source_job: str
    target_job: str
    relation_type: str
    success_rate: float = 0
    time_cost: str = ''
    difficulty: str = 'medium'
    required_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    case_count: int = 0
    weight: float = 0


class TransferPathResult(BaseModel):
    jobs: list[str] = Field(default_factory=list)
    steps: int = 0
    cumulative_success_rate: float = 0
    estimated_time_cost: str = ''
    difficulty: str = 'medium'
    ready_ratio: float = 0
    is_feasible: bool = False
    missing_skills: list[str] = Field(default_factory=list)
    edge_chain: list[TransferPathEdge] = Field(default_factory=list)


class PathEvidenceResponse(BaseModel):
    path_jobs: list[str] = Field(default_factory=list)
    edge_chain: list[TransferPathEdge] = Field(default_factory=list)
    aggregated_required_skills: list[str] = Field(default_factory=list)
    aggregated_missing_skills: list[str] = Field(default_factory=list)
    evidence_sources: list[str] = Field(default_factory=list)


class TransferPathQueryRequest(BaseModel):
    from_job: str
    to_job: str
    max_steps: int = 5


class PersonalizedPathQueryRequest(BaseModel):
    from_job: str
    student_skills: list[str] = Field(default_factory=list)
    target_job: Optional[str] = None
    max_steps: int = 5
    limit: int = 10


class PathEvidenceRequest(BaseModel):
    path_jobs: list[str] = Field(default_factory=list)
    student_skills: list[str] = Field(default_factory=list)


class PersonalizedSubgraphRequest(BaseModel):
    focus_job: str
    target_job: Optional[str] = None
    recommended_jobs: list[str] = Field(default_factory=list)
    student_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    max_paths: int = 3


class GraphEntityDetailRequest(BaseModel):
    entity_id: str
    node_type: str = 'job_family'


class RelatedJobsRequest(BaseModel):
    job: str
    limit: int = 5


class EntryPointsRequest(BaseModel):
    target_job: str
    max_steps: int = 5


class JobInfluenceItem(BaseModel):
    job: str
    influence_score: float


class JobInfluenceResponse(BaseModel):
    ranking: list[JobInfluenceItem] = Field(default_factory=list)


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
    industry_trend: Optional[IndustryTrendAnalysis] = None


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
