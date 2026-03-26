from fastapi import APIRouter, Depends

from backend.app.dependencies import get_rag_chunker, get_rag_embedder, get_rag_evaluator, get_rag_retriever, get_rag_store
from backend.app.repositories.rag_store import FileRagStore
from backend.app.schemas.rag import (
    RagEvaluationRequest,
    RagEvaluationSummary,
    RagIngestRequest,
    RagIngestResponse,
    RagSearchRequest,
    RagSearchResponse,
    RagStoreStats,
)
from backend.app.services.rag_evaluator import RagEvaluationService
from backend.app.services.rag_retrieval import RagRetrievalService


router = APIRouter()


@router.get('/stats', response_model=RagStoreStats)
def get_rag_stats(store: FileRagStore = Depends(get_rag_store)) -> RagStoreStats:
    return store.get_stats()


@router.post('/ingest', response_model=RagIngestResponse)
def ingest_rag_documents(
    request: RagIngestRequest,
    store: FileRagStore = Depends(get_rag_store),
    chunker=Depends(get_rag_chunker),
    embedder=Depends(get_rag_embedder),
) -> RagIngestResponse:
    return store.upsert_documents(request.documents, chunker, embedder, reset_store=request.reset_store)


@router.post('/search', response_model=RagSearchResponse)
def search_rag(
    request: RagSearchRequest,
    retriever: RagRetrievalService = Depends(get_rag_retriever),
) -> RagSearchResponse:
    return retriever.search(request)


@router.post('/evaluate', response_model=RagEvaluationSummary)
def evaluate_rag(
    request: RagEvaluationRequest,
    evaluator: RagEvaluationService = Depends(get_rag_evaluator),
) -> RagEvaluationSummary:
    return evaluator.evaluate(request)
