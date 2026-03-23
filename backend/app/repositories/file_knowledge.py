import json
from pathlib import Path

from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.graph import JobGraph
from backend.app.schemas.job import JobRequirementProfile


class FileKnowledgeRepository(KnowledgeRepository):
    def __init__(self, artifact_dir: str) -> None:
        self.artifact_dir = Path(artifact_dir)
        self.profile_path = self.artifact_dir / 'job_profiles.json'
        self.graph_path = self.artifact_dir / 'job_graph.json'
        self._profiles = self._load_profiles()
        self._graph = self._load_graph()

    @classmethod
    def is_available(cls, artifact_dir: str) -> bool:
        path = Path(artifact_dir)
        return (path / 'job_profiles.json').exists() and (path / 'job_graph.json').exists()

    def list_job_families(self) -> list[JobRequirementProfile]:
        return list(self._profiles.values())

    def get_job_family(self, job_family: str):
        return self._profiles.get(job_family)

    def get_skill_lexicon(self) -> list[str]:
        skills: set[str] = set()
        for job in self._profiles.values():
            skills.update(job.required_skills)
            skills.update(job.bonus_skills)
        return sorted(skills)

    def get_soft_skill_lexicon(self) -> list[str]:
        skills: set[str] = set()
        for job in self._profiles.values():
            skills.update(job.soft_skills)
        return sorted(skills)

    def get_job_graph(self) -> JobGraph:
        return self._graph

    def _load_profiles(self) -> dict[str, JobRequirementProfile]:
        payload = json.loads(self.profile_path.read_text(encoding='utf-8'))
        return {
            item['job_family']: JobRequirementProfile(**item)
            for item in payload
        }

    def _load_graph(self) -> JobGraph:
        payload = json.loads(self.graph_path.read_text(encoding='utf-8'))
        return JobGraph(**payload)
