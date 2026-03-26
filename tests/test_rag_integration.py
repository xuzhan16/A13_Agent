import os
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.dependencies import (
    get_industry_trend_service,
    get_llm_client,
    get_orchestrator,
    get_rag_chunker,
    get_rag_embedder,
    get_rag_evaluator,
    get_rag_evidence_service,
    get_rag_graph_bridge,
    get_rag_retriever,
    get_rag_store,
    get_repository,
    get_resume_parser,
    get_resume_structurer,
    get_soft_skill_assessor,
)
from backend.app.main import create_app
from backend.app.schemas.rag import RagDocumentInput, RagDocumentMetadata


SAMPLE_REQUEST = {
    'intake': {
        'basic_info': {
            'name': 'Student C',
            'school': 'Demo University',
            'major': 'Software Engineering',
            'degree': 'Bachelor',
            'graduation_year': 2026,
        },
        'preference': {
            'target_roles': ['Java?????'],
            'target_cities': ['??'],
            'desired_industries': ['???'],
            'prefer_stability': False,
            'prefer_innovation': True,
        },
        'resume_text': 'Java Spring Boot MySQL Redis project experience with Linux commands and backend API development.',
        'self_description': 'Fast learner and good communicator.',
        'manual_skills': ['Java', 'Spring Boot', 'MySQL', 'Redis'],
        'project_experiences': ['Built Java backend system with cache optimization and API design.'],
        'internship_experiences': ['Worked on enterprise backend requirement analysis and bug fixing.'],
        'campus_experiences': ['Led a student tech club and organized demos.'],
        'certificates': ['CET-4'],
        'follow_up_answers': [],
    },
    'preferred_job_family': 'Java?????',
    'top_k_matches': 3,
    'max_follow_up_questions': 3,
}


def _clear_caches() -> None:
    for func in [
        get_settings,
        get_repository,
        get_llm_client,
        get_rag_store,
        get_rag_embedder,
        get_rag_chunker,
        get_rag_retriever,
        get_rag_graph_bridge,
        get_rag_evaluator,
        get_rag_evidence_service,
        get_resume_parser,
        get_resume_structurer,
        get_soft_skill_assessor,
        get_industry_trend_service,
        get_orchestrator,
    ]:
        func.cache_clear()


def test_report_contains_rag_references_and_api_search() -> None:
    with TemporaryDirectory() as tmp_dir:
        previous = {key: os.environ.get(key) for key in ['ENABLE_RAG', 'RAG_STORE_DIR', 'ENABLE_LLM', 'KNOWLEDGE_SOURCE']}
        os.environ['ENABLE_RAG'] = 'true'
        os.environ['RAG_STORE_DIR'] = tmp_dir
        os.environ['ENABLE_LLM'] = 'false'
        os.environ['KNOWLEDGE_SOURCE'] = 'file'
        _clear_caches()
        try:
            store = get_rag_store()
            store.upsert_documents(
                [
                    RagDocumentInput(
                        document_id='industry-java-02',
                        title='Java 3-year trend',
                        text='Java developers need Docker, Kubernetes, CI/CD and AI integration to stay competitive over the next three years.',
                        metadata=RagDocumentMetadata(
                            source_type='industry_report',
                            source_uri='report://java-3y',
                            job_families=['Java?????'],
                            skills=['Docker', 'Kubernetes', 'CI/CD', 'AI integration'],
                            tags=['trend'],
                            trust_score=0.92,
                        ),
                    ),
                    RagDocumentInput(
                        document_id='skill-docker-01',
                        title='Docker skill premium',
                        text='Docker appears in backend and cloud native jobs, with clear salary premium for engineering and deployment roles.',
                        metadata=RagDocumentMetadata(
                            source_type='skill_trend',
                            source_uri='trend://docker',
                            job_families=['Java?????'],
                            skills=['Docker'],
                            tags=['skill'],
                            trust_score=0.88,
                        ),
                    ),
                ],
                get_rag_chunker(),
                get_rag_embedder(),
                reset_store=True,
            )

            client = TestClient(create_app())
            report_response = client.post('/api/v1/planning/report', json=SAMPLE_REQUEST)
            assert report_response.status_code == 200
            payload = report_response.json()
            assert payload['metadata']['rag_enabled'] is True
            assert payload['student_profile']['retrieved_references']
            assert payload['report']['references']
            assert payload['report']['industry_trend']['citations']
            assert 'RAG????' in payload['report']['report_markdown']

            search_response = client.post(
                '/api/v1/rag/search',
                json={
                    'query': 'Java Docker Kubernetes AI integration',
                    'top_k': 3,
                    'filters': {
                        'source_types': ['industry_report', 'skill_trend'],
                        'job_families': ['Java?????'],
                    },
                },
            )
            assert search_response.status_code == 200
            assert search_response.json()['citations']
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            _clear_caches()
