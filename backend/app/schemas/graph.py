from typing import Optional

from pydantic import BaseModel, Field


class JobGraphNode(BaseModel):
    id: str
    label: str
    node_type: str
    sample_count: int = 0
    top_skills: list[str] = Field(default_factory=list)
    top_cities: list[str] = Field(default_factory=list)
    top_industries: list[str] = Field(default_factory=list)
    description: str = ''
    highlight: str = ''
    badges: list[str] = Field(default_factory=list)
    score: float = 0


class JobGraphEdge(BaseModel):
    source: str
    target: str
    edge_type: str
    weight: float = 0
    reason: str = ''
    success_rate: float = 0
    time_cost: str = ''
    difficulty: str = 'medium'
    required_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    case_count: int = 0
    highlight: str = ''


class GraphRelationPreview(BaseModel):
    target_id: str
    label: str
    node_type: str = 'job_family'
    relation_type: str = ''
    success_rate: float = 0
    time_cost: str = ''
    difficulty: str = 'medium'
    required_skills: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class GraphEntityDetail(BaseModel):
    entity_id: str
    label: str
    node_type: str = 'job_family'
    description: str = ''
    sample_count: int = 0
    top_skills: list[str] = Field(default_factory=list)
    top_cities: list[str] = Field(default_factory=list)
    top_industries: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    bonus_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    certificates: list[str] = Field(default_factory=list)
    practice_requirements: list[str] = Field(default_factory=list)
    vertical_growth_path: list[str] = Field(default_factory=list)
    transfer_paths: list[str] = Field(default_factory=list)
    recommended_jobs: list[str] = Field(default_factory=list)
    entry_paths: list[list[str]] = Field(default_factory=list)
    incoming_relations: list[GraphRelationPreview] = Field(default_factory=list)
    outgoing_relations: list[GraphRelationPreview] = Field(default_factory=list)
    linked_jobs: list[str] = Field(default_factory=list)
    salary_min_monthly: Optional[float] = None
    salary_max_monthly: Optional[float] = None
    influence_score: float = 0
    category: str = ''
    difficulty: str = ''
    market_demand: float = 0
    trend: str = ''
    evidence_snippets: list[str] = Field(default_factory=list)


class PersonalizedGraphSummary(BaseModel):
    focus_job: str = ''
    target_job: str = ''
    recommended_jobs: list[str] = Field(default_factory=list)
    owned_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    selected_path: list[str] = Field(default_factory=list)
    readiness_score: float = 0
    estimated_success_rate: float = 0
    estimated_time_cost: str = ''
    evidence_sources: list[str] = Field(default_factory=list)


class JobGraph(BaseModel):
    nodes: list[JobGraphNode] = Field(default_factory=list)
    edges: list[JobGraphEdge] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    summary: Optional[PersonalizedGraphSummary] = None
