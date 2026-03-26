from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response

from backend.app.agents.orchestrator import CareerPlanningOrchestrator
from backend.app.dependencies import get_orchestrator, get_repository, get_resume_parser, get_resume_structurer
from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.graph import JobGraph
from backend.app.schemas.job import JobRequirementProfile
from backend.app.schemas.planning import (
    CareerPlanningRequest,
    CareerPlanningResponse,
    FollowUpQuestionRequest,
    FollowUpQuestionResponse,
    PathEvidenceRequest,
    PathEvidenceResponse,
    PersonalizedPathQueryRequest,
    PersonalizedSubgraphRequest,
    TransferPathQueryRequest,
    TransferPathResult,
)
from backend.app.schemas.resume import ResumeParseResponse
from backend.app.services.resume_parser import ResumeParserService
from backend.app.services.resume_structurer import ResumeStructuringService

router = APIRouter()


@router.get('/job-families', response_model=List[JobRequirementProfile])
def list_job_families(
    repository: KnowledgeRepository = Depends(get_repository),
) -> List[JobRequirementProfile]:
    return repository.list_job_families()


@router.get('/job-graph', response_model=JobGraph)
def get_job_graph(
    repository: KnowledgeRepository = Depends(get_repository),
) -> JobGraph:
    return repository.get_job_graph()


@router.post('/graph/transfer-paths', response_model=List[TransferPathResult])
def find_transfer_paths(
    request: TransferPathQueryRequest,
    repository: KnowledgeRepository = Depends(get_repository),
) -> List[TransferPathResult]:
    return repository.find_transfer_paths(
        from_job=request.from_job,
        to_job=request.to_job,
        max_steps=request.max_steps,
    )


@router.post('/graph/personalized-paths', response_model=List[TransferPathResult])
def find_personalized_paths(
    request: PersonalizedPathQueryRequest,
    repository: KnowledgeRepository = Depends(get_repository),
) -> List[TransferPathResult]:
    return repository.get_personalized_paths(
        from_job=request.from_job,
        student_skills=request.student_skills,
        target_job=request.target_job,
        max_steps=request.max_steps,
        limit=request.limit,
    )


@router.post('/graph/path-evidence', response_model=PathEvidenceResponse)
def get_path_evidence(
    request: PathEvidenceRequest,
    repository: KnowledgeRepository = Depends(get_repository),
) -> PathEvidenceResponse:
    return repository.get_path_evidence(
        path_jobs=request.path_jobs,
        student_skills=request.student_skills,
    )


@router.post('/graph/personalized-subgraph', response_model=JobGraph)
def get_personalized_subgraph(
    request: PersonalizedSubgraphRequest,
    repository: KnowledgeRepository = Depends(get_repository),
) -> JobGraph:
    return repository.get_personalized_subgraph(
        focus_job=request.focus_job,
        student_skills=request.student_skills,
        target_job=request.target_job,
        recommended_jobs=request.recommended_jobs,
        missing_skills=request.missing_skills,
        max_paths=request.max_paths,
    )


@router.post('/resume/parse', response_model=ResumeParseResponse)
async def parse_resume(
    file: UploadFile = File(...),
    parser: ResumeParserService = Depends(get_resume_parser),
    structurer: ResumeStructuringService = Depends(get_resume_structurer),
) -> ResumeParseResponse:
    content = await file.read()
    parsed = parser.parse(file_name=file.filename or 'resume.txt', content=content)
    structured = structurer.structure(parsed.extracted_text, file_name=file.filename or 'resume.txt')
    payload = parsed.dict()
    payload['structured_profile'] = structured.dict()
    payload['form_fill_suggestion'] = structured.form_fill_suggestion.dict()
    return ResumeParseResponse(**payload)


@router.post('/follow-up-questions', response_model=FollowUpQuestionResponse)
def generate_follow_up_questions(
    request: FollowUpQuestionRequest,
    orchestrator: CareerPlanningOrchestrator = Depends(get_orchestrator),
) -> FollowUpQuestionResponse:
    return orchestrator.suggest_follow_up_questions(request)


@router.post('/report', response_model=CareerPlanningResponse)
def generate_report(
    request: CareerPlanningRequest,
    orchestrator: CareerPlanningOrchestrator = Depends(get_orchestrator),
) -> CareerPlanningResponse:
    return orchestrator.run(request)


@router.post('/report/export-markdown')
def export_report_markdown(
    request: CareerPlanningRequest,
    orchestrator: CareerPlanningOrchestrator = Depends(get_orchestrator),
) -> Response:
    response = orchestrator.run(request)
    student_name = response.student_profile.basic_info.name or 'student'
    ascii_stem = ''.join(ch for ch in student_name if ch.isascii() and (ch.isalnum() or ch in '-_')).strip('_-')
    file_name = f'{ascii_stem or "student"}_career_report.md'
    return Response(
        content=response.report.report_markdown,
        media_type='text/markdown; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{file_name}"'},
    )
