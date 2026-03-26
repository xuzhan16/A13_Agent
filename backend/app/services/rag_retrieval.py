import json
from collections import OrderedDict
from math import sqrt

from backend.app.repositories.rag_store import FileRagStore
from backend.app.schemas.rag import RagCitation, RagSearchFilters, RagSearchRequest, RagSearchResponse
from backend.app.services.rag_embedding import tokenize_text


class RagRetrievalService:
    def __init__(
        self,
        store: FileRagStore,
        embedder,
        default_top_k: int = 5,
        score_threshold: float = 0.18,
        cache_enabled: bool = True,
        cache_size: int = 128,
    ) -> None:
        self.store = store
        self.embedder = embedder
        self.default_top_k = max(1, default_top_k)
        self.score_threshold = max(0.0, score_threshold)
        self.cache_enabled = cache_enabled
        self.cache_size = max(8, cache_size)
        self._cache: OrderedDict[str, RagSearchResponse] = OrderedDict()

    def search(self, request: RagSearchRequest) -> RagSearchResponse:
        query = str(request.query or '').strip()
        top_k = request.top_k or self.default_top_k
        store_version = self.store.get_stats().store_version
        cache_key = self._cache_key(query, request.filters, top_k, store_version)
        if self.cache_enabled and cache_key in self._cache:
            cached = self._cache[cache_key].copy(deep=True)
            cached.cache_hit = True
            return cached

        if not query:
            return RagSearchResponse(query='', store_version=store_version)

        chunks = self.store.list_chunks(request.filters)
        query_vector = self.embedder.embed(query)
        query_terms = set(self.embedder.extract_keywords(query, limit=16) + tokenize_text(query))
        raw_candidates: list[tuple[float, RagCitation]] = []

        for chunk in chunks:
            vector_score = self._cosine(query_vector, chunk.embedding)
            chunk_terms = set(chunk.keywords + tokenize_text(chunk.metadata.title) + tokenize_text(chunk.text[:320]))
            matched_terms = sorted(query_terms.intersection(chunk_terms))[:8]
            lexical_score = round(len(matched_terms) / max(len(query_terms), 1), 4)
            trust_score = min(max(chunk.metadata.trust_score, 0.0), 1.0)
            metadata_bonus = 0.05 if matched_terms and chunk.metadata.source_type in {'industry_report', 'skill_trend'} else 0.0
            rerank_score = round(min(1.0, vector_score * 0.55 + lexical_score * 0.35 + trust_score * 0.10 + metadata_bonus), 4)
            if rerank_score < self.score_threshold and not matched_terms:
                continue
            citation = RagCitation(
                citation_id=f'{chunk.metadata.chunk_id}::citation',
                document_id=chunk.metadata.document_id,
                chunk_id=chunk.metadata.chunk_id,
                title=chunk.metadata.title,
                source_type=chunk.metadata.source_type,
                source_uri=chunk.metadata.source_uri,
                locator=chunk.metadata.locator,
                published_at=chunk.metadata.published_at,
                excerpt=chunk.text[:260],
                score=rerank_score,
                vector_score=round(vector_score, 4),
                lexical_score=lexical_score,
                rerank_score=rerank_score,
                matched_terms=matched_terms,
                rationale=self._build_rationale(matched_terms, chunk.metadata.source_type, trust_score),
            )
            raw_candidates.append((rerank_score, citation))

        raw_candidates.sort(key=lambda item: (-item[0], -item[1].lexical_score, item[1].title))
        citations = [item[1] for item in raw_candidates[:top_k]]
        response = RagSearchResponse(
            query=query,
            citations=citations,
            retrieval_plan=self._build_plan(query, request.filters, len(chunks)),
            total_hits=len(raw_candidates),
            cache_hit=False,
            store_version=store_version,
        )
        if self.cache_enabled:
            self._cache[cache_key] = response.copy(deep=True)
            while len(self._cache) > self.cache_size:
                self._cache.popitem(last=False)
        return response

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        if not left or not right:
            return 0.0
        upper = min(len(left), len(right))
        dot = sum(left[index] * right[index] for index in range(upper))
        left_norm = sqrt(sum(value * value for value in left[:upper]))
        right_norm = sqrt(sum(value * value for value in right[:upper]))
        if left_norm <= 0 or right_norm <= 0:
            return 0.0
        return round(max(0.0, dot / (left_norm * right_norm)), 4)

    @staticmethod
    def _build_plan(query: str, filters: RagSearchFilters, candidate_count: int) -> list[str]:
        steps = [
            f'query={query}',
            'rank=0.55*vector + 0.35*lexical + 0.10*trust',
            f'candidate_chunks={candidate_count}',
        ]
        if filters.source_types:
            steps.append('source_types=' + ','.join(filters.source_types))
        if filters.job_families:
            steps.append('job_families=' + ','.join(filters.job_families))
        if filters.skills:
            steps.append('skills=' + ','.join(filters.skills))
        if filters.tags:
            steps.append('tags=' + ','.join(filters.tags))
        return steps

    @staticmethod
    def _build_rationale(matched_terms: list[str], source_type: str, trust_score: float) -> str:
        matched_text = ', '.join(matched_terms[:5]) if matched_terms else 'semantic-near-match'
        return f'matched_terms={matched_text}; source_type={source_type}; trust={round(trust_score, 2)}'

    @staticmethod
    def _cache_key(query: str, filters: RagSearchFilters, top_k: int, store_version: str) -> str:
        return json.dumps(
            {
                'query': query,
                'filters': filters.dict(),
                'top_k': top_k,
                'store_version': store_version,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
