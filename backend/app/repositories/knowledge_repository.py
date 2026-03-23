from abc import ABC, abstractmethod

from backend.app.schemas.graph import JobGraph
from backend.app.schemas.job import JobRequirementProfile


class KnowledgeRepository(ABC):
    @abstractmethod
    def list_job_families(self) -> list[JobRequirementProfile]:
        raise NotImplementedError

    @abstractmethod
    def get_job_family(self, job_family: str):
        raise NotImplementedError

    @abstractmethod
    def get_skill_lexicon(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def get_soft_skill_lexicon(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def get_job_graph(self) -> JobGraph:
        raise NotImplementedError
