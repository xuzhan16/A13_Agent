from typing import Optional

from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.job import JobRequirementProfile
from backend.app.schemas.student import StudentProfile


class JobProfilerService:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def select_candidate_jobs(
        self,
        student_profile: StudentProfile,
        preferred_job_family: Optional[str],
        top_k: int,
    ) -> list[JobRequirementProfile]:
        jobs = self.repository.list_job_families()
        if preferred_job_family:
            exact = self.repository.get_job_family(preferred_job_family)
            if exact:
                ranked = [exact] + [job for job in jobs if job.job_family != exact.job_family]
                return ranked[:top_k]

        preferred_targets = ' '.join(student_profile.preference.target_roles).lower()
        major = student_profile.basic_info.major.lower()
        scored: list[tuple[int, JobRequirementProfile]] = []
        for job in jobs:
            score = 0
            if job.job_family.lower() in preferred_targets:
                score += 10
            if any(keyword.lower() in major for keyword in job.preferred_majors):
                score += 5
            overlap = len(set(student_profile.hard_skills) & set(job.required_skills))
            score += overlap
            scored.append((score, job))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [job for _, job in scored[:top_k]]
