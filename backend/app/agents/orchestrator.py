from typing import Optional

from backend.app.schemas.planning import (
    CareerPlanningRequest,
    CareerPlanningResponse,
    FollowUpQuestionRequest,
    FollowUpQuestionResponse,
    PlanningMetadata,
)
from backend.app.services.follow_up_question import FollowUpQuestionService
from backend.app.services.job_profiler import JobProfilerService
from backend.app.services.matching import MatchingService
from backend.app.services.path_planner import PathPlannerService
from backend.app.services.report_builder import ReportBuilderService
from backend.app.services.student_profiler import StudentProfilerService


class CareerPlanningOrchestrator:
    def __init__(
        self,
        student_profiler: StudentProfilerService,
        job_profiler: JobProfilerService,
        matching_service: MatchingService,
        path_planner: PathPlannerService,
        report_builder: ReportBuilderService,
        follow_up_service: FollowUpQuestionService,
        llm_enabled: bool = False,
        knowledge_base_source: str = 'unknown',
    ) -> None:
        self.student_profiler = student_profiler
        self.job_profiler = job_profiler
        self.matching_service = matching_service
        self.path_planner = path_planner
        self.report_builder = report_builder
        self.follow_up_service = follow_up_service
        self.llm_enabled = llm_enabled
        self.knowledge_base_source = knowledge_base_source

    def run(self, request: CareerPlanningRequest) -> CareerPlanningResponse:
        student_profile = self.student_profiler.build_profile(request.intake)
        candidate_jobs = self.job_profiler.select_candidate_jobs(
            student_profile=student_profile,
            preferred_job_family=request.preferred_job_family,
            top_k=request.top_k_matches,
        )
        match_results = self.matching_service.rank_jobs(
            student_profile=student_profile,
            candidate_jobs=candidate_jobs,
        )
        path_options = self.path_planner.build_paths(
            student_profile=student_profile,
            match_results=match_results,
        )
        report = self.report_builder.build(
            student_profile=student_profile,
            match_results=match_results,
            path_options=path_options,
        )
        follow_up_questions = self.follow_up_service.generate(
            intake=request.intake,
            student_profile=student_profile,
            match_results=match_results,
            max_questions=request.max_follow_up_questions,
        )
        metadata = self._build_metadata(student_profile.profile_source, report.generation_mode)
        return CareerPlanningResponse(
            student_profile=student_profile,
            match_results=match_results,
            path_options=path_options,
            report=report,
            follow_up_questions=follow_up_questions,
            metadata=metadata,
        )

    def suggest_follow_up_questions(self, request: FollowUpQuestionRequest) -> FollowUpQuestionResponse:
        student_profile = self.student_profiler.build_profile(request.intake)
        candidate_jobs = self.job_profiler.select_candidate_jobs(
            student_profile=student_profile,
            preferred_job_family=request.preferred_job_family,
            top_k=request.top_k_matches,
        )
        match_results = self.matching_service.rank_jobs(
            student_profile=student_profile,
            candidate_jobs=candidate_jobs,
        )
        questions = self.follow_up_service.generate(
            intake=request.intake,
            student_profile=student_profile,
            match_results=match_results,
            max_questions=request.max_questions,
        )
        metadata = self._build_metadata(student_profile.profile_source, report_mode='not_applicable')
        return FollowUpQuestionResponse(
            student_profile=student_profile,
            candidate_job_families=[item.job_family for item in candidate_jobs],
            questions=questions,
            metadata=metadata,
        )

    def _build_metadata(self, profile_mode: str, report_mode: str) -> PlanningMetadata:
        return PlanningMetadata(
            profile_mode=profile_mode,
            report_mode=report_mode,
            llm_enabled=self.llm_enabled,
            knowledge_base_source=self.knowledge_base_source,
        )
