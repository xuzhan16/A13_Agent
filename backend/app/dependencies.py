from functools import lru_cache

from backend.app.agents.orchestrator import CareerPlanningOrchestrator
from backend.app.core.config import get_settings
from backend.app.infra.llm.base import LLMClient, build_llm_client
from backend.app.repositories.file_knowledge import FileKnowledgeRepository
from backend.app.repositories.in_memory_knowledge import InMemoryKnowledgeRepository
from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.services.follow_up_question import FollowUpQuestionService
from backend.app.services.job_profiler import JobProfilerService
from backend.app.services.matching import MatchingService
from backend.app.services.path_planner import PathPlannerService
from backend.app.services.report_builder import ReportBuilderService
from backend.app.services.resume_parser import ResumeParserService
from backend.app.services.student_profiler import StudentProfilerService


@lru_cache()
def get_repository() -> KnowledgeRepository:
    settings = get_settings()
    if FileKnowledgeRepository.is_available(settings.knowledge_base_dir):
        return FileKnowledgeRepository(settings.knowledge_base_dir)
    return InMemoryKnowledgeRepository()


@lru_cache()
def get_llm_client() -> LLMClient:
    settings = get_settings()
    return build_llm_client(
        enable_llm=settings.enable_llm,
        base_url=settings.llm_api_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
    )


@lru_cache()
def get_resume_parser() -> ResumeParserService:
    return ResumeParserService()


@lru_cache()
def get_orchestrator() -> CareerPlanningOrchestrator:
    repository = get_repository()
    llm_client = get_llm_client()
    return CareerPlanningOrchestrator(
        student_profiler=StudentProfilerService(repository, llm_client=llm_client),
        job_profiler=JobProfilerService(repository),
        matching_service=MatchingService(),
        path_planner=PathPlannerService(repository),
        report_builder=ReportBuilderService(llm_client=llm_client),
        follow_up_service=FollowUpQuestionService(llm_client=llm_client),
        llm_enabled=llm_client.enabled,
        knowledge_base_source=type(repository).__name__,
    )
