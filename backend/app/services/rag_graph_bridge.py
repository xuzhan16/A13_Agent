from __future__ import annotations

from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.job import MatchResult
from backend.app.schemas.planning import CareerPathOption
from backend.app.schemas.rag import RagSearchFilters, RagSearchRequest
from backend.app.schemas.student import StudentProfile


class RagGraphBridgeService:
    def __init__(self, repository: KnowledgeRepository, top_k: int = 5) -> None:
        self.repository = repository
        self.top_k = max(1, top_k)

    def build_student_profile_request(self, student_profile: StudentProfile) -> RagSearchRequest:
        target_roles = student_profile.preference.target_roles[:2]
        lead_role = target_roles[0] if target_roles else ''
        query = ' '.join(item for item in [lead_role, 'job requirements', 'core skills', 'market trend'] if item)
        return RagSearchRequest(
            query=query or 'career planning job requirements',
            top_k=min(3, self.top_k),
            filters=RagSearchFilters(
                source_types=['jd', 'industry_report'],
                job_families=target_roles,
            ),
        )

    def build_industry_trend_requests(self, student_profile: StudentProfile, match_results: list[MatchResult]) -> list[tuple[str, str, RagSearchRequest]]:
        del student_profile
        requests: list[tuple[str, str, RagSearchRequest]] = []
        seen_skills: list[str] = []
        for result in match_results[:2]:
            requests.append(
                (
                    f'role-heat::{result.job_family}',
                    f'{result.job_family} market heat',
                    RagSearchRequest(
                        query=' '.join(item for item in [result.job_family, *result.matched_skills[:2], 'hiring demand salary growth trend'] if item),
                        top_k=min(3, self.top_k),
                        filters=RagSearchFilters(
                            source_types=['industry_report', 'jd'],
                            job_families=[result.job_family],
                        ),
                    ),
                )
            )
            for skill in result.missing_skills[:3]:
                if skill in seen_skills:
                    continue
                seen_skills.append(skill)
                requests.append(
                    (
                        f'skill-trend::{skill}',
                        f'{skill} skill trend',
                        RagSearchRequest(
                            query=f'{skill} skill trend hiring growth salary premium {result.job_family}',
                            top_k=min(2, self.top_k),
                            filters=RagSearchFilters(
                                source_types=['skill_trend', 'industry_report', 'jd'],
                                job_families=[result.job_family],
                                skills=[skill],
                            ),
                        ),
                    )
                )
        if not requests:
            requests.append(
                (
                    'industry-generic',
                    'industry generic trend',
                    RagSearchRequest(
                        query='graduate hiring trend skill demand market report',
                        top_k=min(3, self.top_k),
                        filters=RagSearchFilters(source_types=['industry_report']),
                    ),
                )
            )
        return requests

    def build_report_request(
        self,
        student_profile: StudentProfile,
        match_results: list[MatchResult],
        path_options: list[CareerPathOption],
    ) -> RagSearchRequest:
        focus_job = match_results[0].job_family if match_results else ''
        target_job = path_options[0].target_role if path_options else ''
        path_jobs = self._resolve_path_jobs(focus_job, target_job, student_profile.hard_skills, path_options)
        missing_skills = self._unique(
            [
                *(match_results[0].missing_skills[:3] if match_results else []),
                *(path_options[0].missing_skills[:3] if path_options else []),
            ]
        )
        query_parts = [focus_job, target_job, 'career path', 'industry trend', 'skill gap', *missing_skills[:2]]
        return RagSearchRequest(
            query=' '.join(item for item in query_parts if item),
            top_k=self.top_k,
            filters=RagSearchFilters(
                source_types=['industry_report', 'jd', 'skill_trend'],
                job_families=self._unique([focus_job, target_job, *path_jobs]),
                skills=missing_skills[:3],
            ),
        )

    def _resolve_path_jobs(
        self,
        focus_job: str,
        target_job: str,
        student_skills: list[str],
        path_options: list[CareerPathOption],
    ) -> list[str]:
        if path_options and path_options[0].path_jobs:
            return path_options[0].path_jobs
        if focus_job and target_job and target_job != focus_job:
            paths = self.repository.get_personalized_paths(
                from_job=focus_job,
                student_skills=student_skills,
                target_job=target_job,
                max_steps=4,
                limit=1,
            )
            if paths:
                return paths[0].jobs
        return self._unique([focus_job, target_job])

    @staticmethod
    def _unique(items: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for item in items:
            text = str(item or '').strip()
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
        return result
