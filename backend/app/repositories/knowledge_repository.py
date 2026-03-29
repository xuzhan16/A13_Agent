from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Iterable, Optional

from backend.app.schemas.graph import GraphEntityDetail, JobGraph, JobGraphEdge, JobGraphNode, PersonalizedGraphSummary
from backend.app.schemas.job import JobRequirementProfile
from backend.app.schemas.planning import PathEvidenceResponse, TransferPathEdge, TransferPathResult


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

    @abstractmethod
    def get_job_recommendations(self, job: str, limit: int = 5) -> list[JobRequirementProfile]:
        raise NotImplementedError

    @abstractmethod
    def get_job_entry_points(self, target_job: str, max_steps: int = 5) -> list[TransferPathResult]:
        raise NotImplementedError

    @abstractmethod
    def get_job_clusters(self) -> dict[str, list[str]]:
        raise NotImplementedError

    @abstractmethod
    def get_job_influence_ranking(self) -> list[tuple[str, float]]:
        raise NotImplementedError

    @abstractmethod
    def build_job_relationships(self) -> None:
        raise NotImplementedError

    def get_graph_entity_detail(self, entity_id: str, node_type: str = 'job_family') -> GraphEntityDetail:
        raise NotImplementedError

    def supports_dynamic_graph(self) -> bool:
        return False

    def find_transfer_paths(self, from_job: str, to_job: str, max_steps: int = 5) -> list[TransferPathResult]:
        results: list[TransferPathResult] = []
        for jobs, edges in self._enumerate_paths(from_job=from_job, max_steps=max_steps):
            if jobs and jobs[-1] == to_job:
                edge_payloads = [self._edge_payload(edge) for edge in edges]
                results.append(self._build_path_result(jobs, edge_payloads))
        return sorted(results, key=lambda item: (item.steps, -item.cumulative_success_rate))

    def get_personalized_paths(
        self,
        from_job: str,
        student_skills: list[str],
        target_job: Optional[str] = None,
        max_steps: int = 5,
        limit: int = 10,
    ) -> list[TransferPathResult]:
        dedup: dict[tuple[str, ...], TransferPathResult] = {}
        for jobs, edges in self._enumerate_paths(from_job=from_job, max_steps=max_steps):
            if target_job and jobs[-1] != target_job:
                continue
            edge_payloads = [self._edge_payload(edge, student_skills=student_skills) for edge in edges]
            result = self._build_path_result(jobs, edge_payloads, student_skills=student_skills)
            dedup.setdefault(tuple(result.jobs), result)
        ranked = sorted(
            dedup.values(),
            key=lambda item: (not item.is_feasible, -item.ready_ratio, -item.cumulative_success_rate, item.steps),
        )
        return ranked[:limit]

    def get_path_evidence(self, path_jobs: list[str], student_skills: Optional[list[str]] = None) -> PathEvidenceResponse:
        student_skills = student_skills or []
        graph = self.get_job_graph()
        edge_map = {(edge.source, edge.target): edge for edge in graph.edges}
        edge_chain: list[TransferPathEdge] = []
        for index in range(max(len(path_jobs) - 1, 0)):
            edge = edge_map.get((path_jobs[index], path_jobs[index + 1]))
            if edge is None:
                continue
            edge_chain.append(self._edge_payload(edge, student_skills=student_skills))
        aggregated_required = self._unique(skill for edge in edge_chain for skill in edge.required_skills)
        aggregated_missing = self._unique(skill for edge in edge_chain for skill in edge.missing_skills)
        evidence_sources = self._unique(source for edge in edge_chain for source in edge.evidence)
        return PathEvidenceResponse(
            path_jobs=path_jobs,
            edge_chain=edge_chain,
            aggregated_required_skills=aggregated_required,
            aggregated_missing_skills=aggregated_missing,
            evidence_sources=evidence_sources,
        )

    def get_personalized_subgraph(
        self,
        focus_job: str,
        student_skills: list[str],
        target_job: Optional[str] = None,
        recommended_jobs: Optional[list[str]] = None,
        missing_skills: Optional[list[str]] = None,
        max_paths: int = 3,
    ) -> JobGraph:
        recommended_jobs = self._unique([focus_job, *(recommended_jobs or [])])
        selected_paths: list[TransferPathResult] = []

        if target_job and target_job != focus_job:
            selected_paths.extend(
                self.get_personalized_paths(
                    from_job=focus_job,
                    student_skills=student_skills,
                    target_job=target_job,
                    max_steps=5,
                    limit=max_paths,
                )
            )

        if not selected_paths:
            for candidate in recommended_jobs[:max_paths]:
                if candidate == focus_job:
                    continue
                selected_paths.extend(
                    self.get_personalized_paths(
                        from_job=focus_job,
                        student_skills=student_skills,
                        target_job=candidate,
                        max_steps=4,
                        limit=1,
                    )
                )

        if not selected_paths:
            selected_paths.extend(
                self.get_personalized_paths(
                    from_job=focus_job,
                    student_skills=student_skills,
                    target_job=None,
                    max_steps=3,
                    limit=max_paths,
                )
            )

        selected_paths = sorted(
            selected_paths,
            key=lambda item: (not item.is_feasible, -item.ready_ratio, -item.cumulative_success_rate, item.steps),
        )[:max_paths]
        primary = selected_paths[0] if selected_paths else None

        base_graph = self.get_job_graph()
        node_lookup = {node.id: node for node in base_graph.nodes}
        nodes: list[JobGraphNode] = []
        edges: list[JobGraphEdge] = []

        job_ids = self._unique([focus_job, *(recommended_jobs or []), *(primary.jobs if primary else [])])
        for job_id in job_ids:
            nodes.append(self._clone_job_node(node_lookup.get(job_id), job_id, focus_job, target_job, recommended_jobs or [], primary))

        for path in selected_paths:
            for edge in path.edge_chain:
                edges.append(
                    JobGraphEdge(
                        source=edge.source_job,
                        target=edge.target_job,
                        edge_type=edge.relation_type.lower(),
                        weight=edge.weight,
                        reason='Recommended transfer step based on the selected path.',
                        success_rate=edge.success_rate,
                        time_cost=edge.time_cost,
                        difficulty=edge.difficulty,
                        required_skills=edge.required_skills,
                        missing_skills=edge.missing_skills,
                        evidence=edge.evidence,
                        case_count=edge.case_count,
                        highlight='selected_path' if primary and path.jobs == primary.jobs else 'candidate_path',
                    )
                )

        target_profile = self.get_job_family(target_job) if target_job else None
        primary_required = self._unique(skill for path in selected_paths for edge in path.edge_chain for skill in edge.required_skills)
        owned_skills = self._unique(skill for skill in student_skills if skill in primary_required or not primary_required)[:8]
        all_missing_skills = self._unique([*(missing_skills or []), *(primary.missing_skills if primary else [])])
        target_required_skills = self._unique((target_profile.required_skills if target_profile else []) + (target_profile.bonus_skills if target_profile else []))

        for skill in owned_skills:
            skill_id = self._skill_node_id(skill)
            nodes.append(
                JobGraphNode(
                    id=skill_id,
                    label=skill,
                    node_type='skill',
                    description='Skill already evidenced in the student profile.',
                    highlight='owned_skill',
                    badges=['Owned'],
                )
            )
            edges.append(
                JobGraphEdge(
                    source=focus_job,
                    target=skill_id,
                    edge_type='has_skill',
                    reason='Skill already owned by the student.',
                    highlight='owned_skill',
                )
            )

        skill_targets = self._unique(target_required_skills + primary_required + all_missing_skills)
        for skill in skill_targets:
            skill_id = self._skill_node_id(skill)
            highlight = 'missing_skill' if skill in all_missing_skills else 'target_skill'
            badges = ['Gap'] if skill in all_missing_skills else ['Target']
            nodes.append(
                JobGraphNode(
                    id=skill_id,
                    label=skill,
                    node_type='skill',
                    description='Skill referenced by the target role or current path.',
                    highlight=highlight,
                    badges=badges,
                )
            )
            attach_target = target_job or (primary.jobs[-1] if primary and primary.jobs else focus_job)
            edges.append(
                JobGraphEdge(
                    source=attach_target,
                    target=skill_id,
                    edge_type='requires',
                    reason='Skill requirement derived from the target role or path step.',
                    required_skills=[skill],
                    missing_skills=[skill] if skill in all_missing_skills else [],
                    highlight=highlight,
                )
            )

        nodes = self._deduplicate_nodes(nodes)
        edges = self._deduplicate_edges(edges)

        summary = PersonalizedGraphSummary(
            focus_job=focus_job,
            target_job=target_job or (primary.jobs[-1] if primary and primary.jobs else ''),
            recommended_jobs=recommended_jobs,
            owned_skills=owned_skills,
            missing_skills=all_missing_skills,
            selected_path=primary.jobs if primary else [],
            readiness_score=round((primary.ready_ratio if primary else 0) * 100, 1),
            estimated_success_rate=primary.cumulative_success_rate if primary else 0,
            estimated_time_cost=primary.estimated_time_cost if primary else '',
            evidence_sources=self._unique(source for path in selected_paths for edge in path.edge_chain for source in edge.evidence),
        )
        return JobGraph(
            nodes=nodes,
            edges=edges,
            metadata={
                'scope': 'personalized_subgraph',
                'knowledge_source': type(self).__name__,
                'path_count': len(selected_paths),
            },
            summary=summary,
        )

    def _enumerate_paths(self, from_job: str, max_steps: int = 5) -> list[tuple[list[str], list[JobGraphEdge]]]:
        graph = self.get_job_graph()
        adjacency: dict[str, list[JobGraphEdge]] = defaultdict(list)
        for edge in graph.edges:
            adjacency[edge.source].append(edge)

        paths: list[tuple[list[str], list[JobGraphEdge]]] = []

        def walk(current_job: str, current_jobs: list[str], current_edges: list[JobGraphEdge]) -> None:
            if current_edges:
                paths.append((list(current_jobs), list(current_edges)))
            if len(current_edges) >= max_steps:
                return
            for edge in adjacency.get(current_job, []):
                if edge.target in current_jobs:
                    continue
                current_jobs.append(edge.target)
                current_edges.append(edge)
                walk(edge.target, current_jobs, current_edges)
                current_jobs.pop()
                current_edges.pop()

        walk(from_job, [from_job], [])
        return paths

    def _edge_payload(self, edge: JobGraphEdge, student_skills: Optional[list[str]] = None) -> TransferPathEdge:
        student_skill_set = {item.lower() for item in (student_skills or [])}
        source_profile = self.get_job_family(edge.source)
        target_profile = self.get_job_family(edge.target)
        required_skills = list(edge.required_skills) or self._infer_required_skills(source_profile, target_profile)
        missing_skills = [skill for skill in required_skills if skill.lower() not in student_skill_set]
        success_rate = edge.success_rate or self._default_success_rate(edge.edge_type, edge.weight)
        time_cost = edge.time_cost or ('1-2 years' if edge.edge_type == 'vertical' else '1-3 years')
        difficulty = edge.difficulty or self._infer_difficulty(required_skills)
        evidence = list(edge.evidence) or ([edge.reason] if edge.reason else ['Derived from graph relationship'])
        case_count = edge.case_count or self._estimate_case_count(source_profile, target_profile)
        return TransferPathEdge(
            source_job=edge.source,
            target_job=edge.target,
            relation_type=edge.edge_type.upper(),
            success_rate=round(success_rate, 2),
            time_cost=time_cost,
            difficulty=difficulty,
            required_skills=required_skills,
            missing_skills=missing_skills,
            evidence=evidence,
            case_count=case_count,
            weight=edge.weight,
        )

    def _build_path_result(
        self,
        jobs: list[str],
        edge_payloads: list[TransferPathEdge],
        student_skills: Optional[list[str]] = None,
    ) -> TransferPathResult:
        del student_skills
        success_rate = 1.0
        low_months = 0
        high_months = 0
        difficulty_rank = {'low': 0, 'medium': 1, 'high': 2}
        hardest = 'low'
        aggregated_required = self._unique(skill for edge in edge_payloads for skill in edge.required_skills)
        aggregated_missing = self._unique(skill for edge in edge_payloads for skill in edge.missing_skills)

        for edge in edge_payloads:
            success_rate *= max(min(edge.success_rate, 0.99), 0.01)
            low, high = self._parse_time_cost(edge.time_cost)
            low_months += low
            high_months += high
            if difficulty_rank.get(edge.difficulty, 1) > difficulty_rank.get(hardest, 0):
                hardest = edge.difficulty

        ready_ratio = 1.0 if not aggregated_required else round((len(aggregated_required) - len(aggregated_missing)) / len(aggregated_required), 2)
        return TransferPathResult(
            jobs=jobs,
            steps=len(edge_payloads),
            cumulative_success_rate=round(success_rate, 4),
            estimated_time_cost=self._format_time_cost(low_months, high_months),
            difficulty=hardest,
            ready_ratio=ready_ratio,
            is_feasible=len(aggregated_missing) == 0,
            missing_skills=aggregated_missing,
            edge_chain=edge_payloads,
        )

    def _clone_job_node(
        self,
        node: Optional[JobGraphNode],
        job_id: str,
        focus_job: str,
        target_job: Optional[str],
        recommended_jobs: list[str],
        primary: Optional[TransferPathResult],
    ) -> JobGraphNode:
        highlight = ''
        badges: list[str] = []
        if job_id == focus_job:
            highlight = 'focus_job'
            badges.append('Current')
        if target_job and job_id == target_job:
            highlight = 'target_job'
            badges.append('Target')
        if job_id in recommended_jobs and job_id != focus_job:
            badges.append('Recommended')
        if primary and job_id in primary.jobs and 'Path' not in badges:
            badges.append('Path')
        if node is None:
            return JobGraphNode(
                id=job_id,
                label=job_id,
                node_type='job_family',
                description='Personalized graph node',
                highlight=highlight,
                badges=badges,
            )
        cloned = JobGraphNode(**node.dict())
        cloned.highlight = highlight or cloned.highlight
        cloned.badges = self._unique([*cloned.badges, *badges])
        if primary and job_id in primary.jobs:
            cloned.score = round(primary.ready_ratio * 100, 1)
        return cloned

    @staticmethod
    def _skill_node_id(skill: str) -> str:
        return f'skill::{skill}'

    @staticmethod
    def _deduplicate_nodes(nodes: list[JobGraphNode]) -> list[JobGraphNode]:
        by_id: dict[str, JobGraphNode] = {}
        for node in nodes:
            current = by_id.get(node.id)
            if current is None:
                by_id[node.id] = node
                continue
            current.badges = KnowledgeRepository._unique([*current.badges, *node.badges])
            current.highlight = current.highlight or node.highlight
            current.score = max(current.score, node.score)
            current.description = current.description or node.description
        return list(by_id.values())

    @staticmethod
    def _deduplicate_edges(edges: list[JobGraphEdge]) -> list[JobGraphEdge]:
        by_key: dict[tuple[str, str, str], JobGraphEdge] = {}
        for edge in edges:
            key = (edge.source, edge.target, edge.edge_type)
            current = by_key.get(key)
            if current is None:
                by_key[key] = edge
                continue
            current.required_skills = KnowledgeRepository._unique([*current.required_skills, *edge.required_skills])
            current.missing_skills = KnowledgeRepository._unique([*current.missing_skills, *edge.missing_skills])
            current.evidence = KnowledgeRepository._unique([*current.evidence, *edge.evidence])
            current.highlight = current.highlight or edge.highlight
            current.success_rate = max(current.success_rate, edge.success_rate)
        return list(by_key.values())

    @staticmethod
    def _infer_required_skills(
        source_profile: Optional[JobRequirementProfile],
        target_profile: Optional[JobRequirementProfile],
    ) -> list[str]:
        if target_profile is None:
            return []
        source_skills = set((source_profile.required_skills if source_profile else []) + (source_profile.bonus_skills if source_profile else []))
        target_skills = list(dict.fromkeys(target_profile.required_skills + target_profile.bonus_skills))
        diff = [skill for skill in target_skills if skill not in source_skills]
        return diff[:4]

    @staticmethod
    def _default_success_rate(edge_type: str, weight: float) -> float:
        normalized_weight = weight or (1.0 if edge_type == 'vertical' else 0.45)
        base = 0.68 if edge_type == 'vertical' else 0.52
        return min(0.95, base + normalized_weight * 0.18)

    @staticmethod
    def _infer_difficulty(required_skills: list[str]) -> str:
        if len(required_skills) >= 4:
            return 'high'
        if len(required_skills) >= 2:
            return 'medium'
        return 'low'

    @staticmethod
    def _estimate_case_count(
        source_profile: Optional[JobRequirementProfile],
        target_profile: Optional[JobRequirementProfile],
    ) -> int:
        source_count = source_profile.sample_count if source_profile else 0
        target_count = target_profile.sample_count if target_profile else 0
        baseline = min([value for value in [source_count, target_count] if value > 0] or [0])
        return int(baseline / 10) if baseline else 0

    @staticmethod
    def _parse_time_cost(value: str) -> tuple[int, int]:
        text = str(value or '').strip().lower()
        if not text:
            return 12, 24
        digits = [int(item) for item in ''.join(ch if ch.isdigit() else ' ' for ch in text).split()]
        if not digits:
            return 12, 24
        if len(digits) == 1:
            digits = [digits[0], digits[0]]
        is_month = 'month' in text
        if is_month:
            return digits[0], digits[1]
        return digits[0] * 12, digits[1] * 12

    @staticmethod
    def _format_time_cost(low_months: int, high_months: int) -> str:
        if low_months <= 0 and high_months <= 0:
            return '1-2 years'
        if high_months <= 12:
            return f'{low_months:g}-{high_months:g} months'
        low_years = round(low_months / 12, 1)
        high_years = round(high_months / 12, 1)
        return f'{low_years:g}-{high_years:g} years'

    @staticmethod
    def _unique(items: Iterable[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for item in items:
            text = str(item).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
        return result
