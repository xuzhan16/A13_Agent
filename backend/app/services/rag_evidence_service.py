from backend.app.schemas.job import MatchResult
from backend.app.schemas.planning import CareerPathOption
from backend.app.schemas.rag import RagCitation, RagEvidenceBundle, RagSearchRequest
from backend.app.schemas.student import StudentProfile
from backend.app.services.rag_graph_bridge import RagGraphBridgeService
from backend.app.services.rag_retrieval import RagRetrievalService


class RagEvidenceService:
    def __init__(self, retriever: RagRetrievalService, graph_bridge: RagGraphBridgeService, enabled: bool = False) -> None:
        self.retriever = retriever
        self.graph_bridge = graph_bridge
        self.enabled = enabled

    def build_student_profile_bundle(self, student_profile: StudentProfile) -> RagEvidenceBundle:
        request = self.graph_bridge.build_student_profile_request(student_profile)
        return self._execute_bundle('student-profile', 'student profile context', request)

    def build_industry_trend_bundles(self, student_profile: StudentProfile, match_results: list[MatchResult]) -> list[RagEvidenceBundle]:
        bundles: list[RagEvidenceBundle] = []
        for bundle_id, topic, request in self.graph_bridge.build_industry_trend_requests(student_profile, match_results):
            bundles.append(self._execute_bundle(bundle_id, topic, request))
        return bundles

    def build_report_bundle(
        self,
        student_profile: StudentProfile,
        match_results: list[MatchResult],
        path_options: list[CareerPathOption],
    ) -> RagEvidenceBundle:
        request = self.graph_bridge.build_report_request(student_profile, match_results, path_options)
        return self._execute_bundle('career-report', 'career report evidence', request)

    @staticmethod
    def flatten_citations(*groups: list[RagCitation]) -> list[RagCitation]:
        result: list[RagCitation] = []
        seen: set[str] = set()
        for group in groups:
            for citation in group:
                key = citation.chunk_id or citation.document_id or citation.citation_id
                if not key or key in seen:
                    continue
                seen.add(key)
                result.append(citation)
        return result

    def _execute_bundle(self, bundle_id: str, topic: str, request: RagSearchRequest) -> RagEvidenceBundle:
        if not self.enabled:
            return RagEvidenceBundle(bundle_id=bundle_id, topic=topic, query=request.query, summary='rag_disabled')
        response = self.retriever.search(request)
        summary = self._summarize(topic, response.citations)
        return RagEvidenceBundle(
            bundle_id=bundle_id,
            topic=topic,
            query=request.query,
            citations=response.citations,
            summary=summary,
            retrieval_plan=response.retrieval_plan,
        )

    @staticmethod
    def _summarize(topic: str, citations: list[RagCitation]) -> str:
        if not citations:
            return f'{topic}: no external evidence found.'
        source_types = sorted({item.source_type for item in citations if item.source_type})
        return f'{topic}: {len(citations)} evidence chunk(s) from {", ".join(source_types)}.'
