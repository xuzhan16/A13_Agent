from pydantic import BaseModel, Field

from backend.app.schemas.job import JobRequirementProfile, MatchResult
from backend.app.schemas.planning import CareerPathOption, CareerReport
from backend.app.schemas.student import StudentProfile


class CareerPlanningState(BaseModel):
    student_profile: StudentProfile
    candidate_jobs: list[JobRequirementProfile] = Field(default_factory=list)
    match_results: list[MatchResult] = Field(default_factory=list)
    path_options: list[CareerPathOption] = Field(default_factory=list)
    report: CareerReport
