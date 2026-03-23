from backend.app.core.catalog import JOB_FAMILY_TEMPLATES
from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.graph import JobGraph, JobGraphEdge, JobGraphNode
from backend.app.schemas.job import JobRequirementProfile


class InMemoryKnowledgeRepository(KnowledgeRepository):
    def __init__(self) -> None:
        self._jobs = {
            template.job_family: JobRequirementProfile(
                job_family=template.job_family,
                description=template.description,
                preferred_majors=list(template.preferred_majors),
                required_skills=list(template.required_skills),
                bonus_skills=list(template.bonus_skills),
                soft_skills=list(template.soft_skills),
                certificates=list(template.certificates),
                practice_requirements=list(template.practice_requirements),
                vertical_growth_path=list(template.vertical_growth_path),
                transfer_paths=list(template.transfer_paths),
                aliases=list(template.aliases),
                source_titles=list(template.aliases),
                sample_count=0,
            )
            for template in JOB_FAMILY_TEMPLATES
        }
        self._graph = self._build_graph()

    def list_job_families(self) -> list[JobRequirementProfile]:
        return list(self._jobs.values())

    def get_job_family(self, job_family: str):
        return self._jobs.get(job_family)

    def get_skill_lexicon(self) -> list[str]:
        skills: set[str] = set()
        for job in self._jobs.values():
            skills.update(job.required_skills)
            skills.update(job.bonus_skills)
        return sorted(skills)

    def get_soft_skill_lexicon(self) -> list[str]:
        skills: set[str] = set()
        for job in self._jobs.values():
            skills.update(job.soft_skills)
        return sorted(skills)

    def get_job_graph(self) -> JobGraph:
        return self._graph

    def _build_graph(self) -> JobGraph:
        nodes: list[JobGraphNode] = []
        edges: list[JobGraphEdge] = []
        node_ids: set[str] = set()

        def add_node(node_id: str, label: str, node_type: str) -> None:
            if node_id in node_ids:
                return
            node_ids.add(node_id)
            nodes.append(JobGraphNode(id=node_id, label=label, node_type=node_type))

        for job in self._jobs.values():
            add_node(job.job_family, job.job_family, 'job_family')
            previous = job.job_family
            for role in job.vertical_growth_path[1:]:
                add_node(role, role, 'career_stage')
                edges.append(
                    JobGraphEdge(
                        source=previous,
                        target=role,
                        edge_type='vertical',
                        weight=1.0,
                        reason='样例岗位库中的纵向发展路径。',
                    )
                )
                previous = role
            for transfer in job.transfer_paths:
                add_node(transfer, transfer, 'job_family' if transfer in self._jobs else 'career_stage')
                edges.append(
                    JobGraphEdge(
                        source=job.job_family,
                        target=transfer,
                        edge_type='transfer',
                        weight=0.4,
                        reason='样例岗位库中的横向转岗路径。',
                    )
                )
        return JobGraph(nodes=nodes, edges=edges, metadata={'source': 'in_memory'})
