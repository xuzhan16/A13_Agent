from tempfile import TemporaryDirectory

from backend.app.repositories.rag_store import FileRagStore
from backend.app.schemas.rag import (
    RagDocumentInput,
    RagDocumentMetadata,
    RagEvaluationRequest,
    RagEvaluationSample,
    RagSearchFilters,
    RagSearchRequest,
)
from backend.app.services.rag_chunker import RagChunker
from backend.app.services.rag_embedding import HashEmbeddingService
from backend.app.services.rag_evaluator import RagEvaluationService
from backend.app.services.rag_retrieval import RagRetrievalService


def test_rag_ingest_search_and_evaluate() -> None:
    with TemporaryDirectory() as tmp_dir:
        store = FileRagStore(tmp_dir)
        chunker = RagChunker(chunk_size=180, overlap=30)
        embedder = HashEmbeddingService(dimension=128)
        response = store.upsert_documents(
            [
                RagDocumentInput(
                    document_id='industry-java-01',
                    title='Java backend trend report',
                    text='Java backend roles now require cloud native, Docker, Kubernetes and AI API integration. Salary premium grows for engineers who can connect LLM services.',
                    metadata=RagDocumentMetadata(
                        source_type='industry_report',
                        source_uri='report://java-trend',
                        job_families=['Java?????'],
                        skills=['Docker', 'Kubernetes', 'AI API'],
                        tags=['trend'],
                        trust_score=0.9,
                    ),
                ),
                RagDocumentInput(
                    document_id='jd-java-01',
                    title='Java developer JD',
                    text='We need Java, Spring Boot, MySQL, Redis, Linux and CI/CD. Bonus skills include Docker and message queue experience.',
                    metadata=RagDocumentMetadata(
                        source_type='jd',
                        source_uri='jd://java-001',
                        job_families=['Java?????'],
                        skills=['Java', 'Spring Boot', 'Docker', 'CI/CD'],
                        tags=['campus'],
                        trust_score=0.8,
                    ),
                ),
            ],
            chunker,
            embedder,
            reset_store=True,
        )
        assert response.ingested_documents == 2
        assert response.ingested_chunks >= 2

        retriever = RagRetrievalService(store, embedder, default_top_k=3, score_threshold=0.05)
        search_response = retriever.search(
            RagSearchRequest(
                query='Java ??? AI API ????',
                top_k=3,
                filters=RagSearchFilters(source_types=['industry_report', 'jd'], job_families=['Java?????']),
            )
        )
        assert search_response.citations
        assert any(item.document_id == 'industry-java-01' for item in search_response.citations)
        assert search_response.retrieval_plan

        evaluator = RagEvaluationService(retriever)
        evaluation = evaluator.evaluate(
            RagEvaluationRequest(
                samples=[
                    RagEvaluationSample(
                        query='Java AI API cloud native trend',
                        relevant_document_ids=['industry-java-01'],
                        filters=RagSearchFilters(source_types=['industry_report']),
                    )
                ],
                top_k=3,
            )
        )
        assert evaluation.sample_count == 1
        assert evaluation.mean_hit_at_k == 1.0
        assert evaluation.mean_mrr > 0
