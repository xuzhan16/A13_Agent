from backend.app.schemas.rag import RagEvaluationRequest, RagEvaluationResult, RagEvaluationSummary, RagSearchRequest
from backend.app.services.rag_retrieval import RagRetrievalService


class RagEvaluationService:
    def __init__(self, retriever: RagRetrievalService) -> None:
        self.retriever = retriever

    def evaluate(self, request: RagEvaluationRequest) -> RagEvaluationSummary:
        results: list[RagEvaluationResult] = []
        for sample in request.samples:
            response = self.retriever.search(
                RagSearchRequest(
                    query=sample.query,
                    top_k=request.top_k,
                    filters=sample.filters,
                )
            )
            ranked_document_ids = [item.document_id for item in response.citations]
            hit = 1.0 if any(item in sample.relevant_document_ids for item in ranked_document_ids) else 0.0
            reciprocal_rank = 0.0
            for index, document_id in enumerate(ranked_document_ids, start=1):
                if document_id in sample.relevant_document_ids:
                    reciprocal_rank = round(1.0 / index, 4)
                    break
            results.append(
                RagEvaluationResult(
                    query=sample.query,
                    hit_at_k=hit,
                    mrr=reciprocal_rank,
                    matched_document_ids=ranked_document_ids,
                    top_citations=response.citations,
                )
            )

        sample_count = len(results)
        mean_hit = round(sum(item.hit_at_k for item in results) / sample_count, 4) if results else 0.0
        mean_mrr = round(sum(item.mrr for item in results) / sample_count, 4) if results else 0.0
        return RagEvaluationSummary(
            top_k=request.top_k,
            sample_count=sample_count,
            mean_hit_at_k=mean_hit,
            mean_mrr=mean_mrr,
            results=results,
        )
