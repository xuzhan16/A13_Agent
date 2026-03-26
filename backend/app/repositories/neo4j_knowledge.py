from __future__ import annotations

from typing import Any, Optional

try:
    from neo4j import GraphDatabase
except Exception:  # pragma: no cover - optional dependency at runtime
    GraphDatabase = None

from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.graph import JobGraph, JobGraphEdge, JobGraphNode
from backend.app.schemas.job import JobRequirementProfile
from backend.app.schemas.planning import PathEvidenceResponse, TransferPathEdge, TransferPathResult


class Neo4jKnowledgeRepository(KnowledgeRepository):
    def __init__(self, uri: str, user: str, password: str, database: str = 'neo4j') -> None:
        if GraphDatabase is None:
            raise ImportError('neo4j package is required. Run `pip install -e .` to install project dependencies.')
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._database = database

    def close(self) -> None:
        self._driver.close()

    def supports_dynamic_graph(self) -> bool:
        return True

    def list_job_families(self) -> list[JobRequirementProfile]:
        query = """
        MATCH (j:Job)
        WHERE coalesce(j.node_type, 'job_family') = 'job_family'
        RETURN j
        ORDER BY coalesce(j.sample_count, 0) DESC, j.name ASC
        """
        return [self._profile_from_props(record['j']) for record in self._run_query(query)]

    def get_job_family(self, job_family: str) -> Optional[JobRequirementProfile]:
        query = """
        MATCH (j:Job {name: $job_family})
        RETURN j
        LIMIT 1
        """
        records = self._run_query(query, {'job_family': job_family})
        if not records:
            return None
        return self._profile_from_props(records[0]['j'])

    def get_skill_lexicon(self) -> list[str]:
        query = 'MATCH (s:Skill) RETURN s.name AS name ORDER BY name'
        return [record['name'] for record in self._run_query(query)]

    def get_soft_skill_lexicon(self) -> list[str]:
        query = 'MATCH (a:Ability) RETURN a.name AS name ORDER BY name'
        return [record['name'] for record in self._run_query(query)]

    def get_job_graph(self) -> JobGraph:
        node_query = """
        MATCH (j:Job)
        RETURN j.name AS id,
               coalesce(j.label, j.name) AS label,
               coalesce(j.node_type, 'job_family') AS node_type,
               coalesce(j.sample_count, 0) AS sample_count,
               coalesce(j.top_skills, []) AS top_skills,
               coalesce(j.top_cities, []) AS top_cities,
               coalesce(j.description, '') AS description
        ORDER BY sample_count DESC, label ASC
        """
        edge_query = """
        MATCH (source:Job)-[rel:TRANSFER_TO|VERTICAL_TO]->(target:Job)
        RETURN source.name AS source,
               target.name AS target,
               CASE type(rel)
                   WHEN 'TRANSFER_TO' THEN 'transfer'
                   ELSE 'vertical'
               END AS edge_type,
               coalesce(rel.weight, 0.0) AS weight,
               coalesce(rel.reason, '') AS reason,
               coalesce(rel.success_rate, 0.0) AS success_rate,
               coalesce(rel.time_cost, '') AS time_cost,
               coalesce(rel.difficulty, 'medium') AS difficulty,
               coalesce(rel.required_skills, []) AS required_skills,
               coalesce(rel.evidence, []) AS evidence,
               coalesce(rel.case_count, 0) AS case_count
        ORDER BY source, target
        """
        nodes = [JobGraphNode(**record) for record in self._run_query(node_query)]
        edges = [JobGraphEdge(**record) for record in self._run_query(edge_query)]
        return JobGraph(
            nodes=nodes,
            edges=edges,
            metadata={
                'source': 'neo4j',
                'node_count': len(nodes),
                'edge_count': len(edges),
            },
        )

    def find_transfer_paths(self, from_job: str, to_job: str, max_steps: int = 5) -> list[TransferPathResult]:
        query = self._build_path_query(max_steps=max_steps, target_required=True)
        records = self._run_query(query, {'from_job': from_job, 'to_job': to_job})
        results = [self._path_result_from_record(record) for record in records]
        return sorted(results, key=lambda item: (item.steps, -item.cumulative_success_rate))

    def get_personalized_paths(
        self,
        from_job: str,
        student_skills: list[str],
        target_job: Optional[str] = None,
        max_steps: int = 5,
        limit: int = 10,
    ) -> list[TransferPathResult]:
        query = self._build_path_query(max_steps=max_steps, target_required=bool(target_job))
        params: dict[str, Any] = {'from_job': from_job}
        if target_job:
            params['to_job'] = target_job
        records = self._run_query(query, params)
        dedup: dict[tuple[str, ...], TransferPathResult] = {}
        for record in records:
            result = self._path_result_from_record(record, student_skills=student_skills)
            dedup.setdefault(tuple(result.jobs), result)
        ranked = sorted(
            dedup.values(),
            key=lambda item: (not item.is_feasible, -item.ready_ratio, -item.cumulative_success_rate, item.steps),
        )
        return ranked[:limit]

    def get_path_evidence(self, path_jobs: list[str], student_skills: Optional[list[str]] = None) -> PathEvidenceResponse:
        student_skills = student_skills or []
        if len(path_jobs) < 2:
            return PathEvidenceResponse(path_jobs=path_jobs)
        pairs = [
            {'step': index, 'source': path_jobs[index], 'target': path_jobs[index + 1]}
            for index in range(len(path_jobs) - 1)
        ]
        query = """
        UNWIND $pairs AS pair
        MATCH (source:Job {name: pair.source})-[rel:TRANSFER_TO|VERTICAL_TO]->(target:Job {name: pair.target})
        RETURN pair.step AS step,
               {
                   source_job: source.name,
                   target_job: target.name,
                   relation_type: type(rel),
                   success_rate: coalesce(rel.success_rate, 0.0),
                   time_cost: coalesce(rel.time_cost, ''),
                   difficulty: coalesce(rel.difficulty, 'medium'),
                   required_skills: coalesce(rel.required_skills, []),
                   evidence: coalesce(rel.evidence, []),
                   case_count: coalesce(rel.case_count, 0),
                   weight: coalesce(rel.weight, 0.0)
               } AS edge
        ORDER BY step ASC
        """
        records = self._run_query(query, {'pairs': pairs})
        edge_chain = [self._edge_from_data(record['edge'], student_skills=student_skills) for record in records]
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

    def _path_result_from_record(
        self,
        record: dict[str, Any],
        student_skills: Optional[list[str]] = None,
    ) -> TransferPathResult:
        edges = [self._edge_from_data(edge, student_skills=student_skills) for edge in record['edge_chain']]
        return self._build_path_result(record['jobs'], edges, student_skills=student_skills)

    def _edge_from_data(self, payload: dict[str, Any], student_skills: Optional[list[str]] = None) -> TransferPathEdge:
        student_skill_set = {item.lower() for item in (student_skills or [])}
        relation_type = str(payload.get('relation_type') or 'TRANSFER_TO').upper()
        required_skills = list(payload.get('required_skills') or [])
        missing_skills = [skill for skill in required_skills if skill.lower() not in student_skill_set]
        return TransferPathEdge(
            source_job=payload.get('source_job', ''),
            target_job=payload.get('target_job', ''),
            relation_type=relation_type,
            success_rate=round(float(payload.get('success_rate') or 0.0), 2),
            time_cost=str(payload.get('time_cost') or ''),
            difficulty=str(payload.get('difficulty') or 'medium'),
            required_skills=required_skills,
            missing_skills=missing_skills,
            evidence=list(payload.get('evidence') or []),
            case_count=int(payload.get('case_count') or 0),
            weight=float(payload.get('weight') or 0.0),
        )

    def _build_path_query(self, max_steps: int, target_required: bool) -> str:
        hops = max(1, min(int(max_steps), 8))
        end_clause = '(end:Job {name: $to_job})' if target_required else '(end:Job)'
        return f"""
        MATCH path = (start:Job {{name: $from_job}})-[:TRANSFER_TO|VERTICAL_TO*1..{hops}]->{end_clause}
        WHERE all(node IN nodes(path) WHERE single(other IN nodes(path) WHERE other = node))
        WITH path, nodes(path) AS ns, relationships(path) AS rels
        RETURN [node IN ns | node.name] AS jobs,
               [rel IN rels | {{
                   source_job: startNode(rel).name,
                   target_job: endNode(rel).name,
                   relation_type: type(rel),
                   success_rate: coalesce(rel.success_rate, 0.0),
                   time_cost: coalesce(rel.time_cost, ''),
                   difficulty: coalesce(rel.difficulty, 'medium'),
                   required_skills: coalesce(rel.required_skills, []),
                   evidence: coalesce(rel.evidence, []),
                   case_count: coalesce(rel.case_count, 0),
                   weight: coalesce(rel.weight, 0.0)
               }}] AS edge_chain,
               length(path) AS steps,
               reduce(score = 1.0, rel IN rels | score * coalesce(rel.success_rate, 0.5)) AS path_score
        ORDER BY steps ASC, path_score DESC
        """

    def _profile_from_props(self, props: Any) -> JobRequirementProfile:
        data = dict(props)
        return JobRequirementProfile(
            job_family=data.get('name', ''),
            description=data.get('description', ''),
            preferred_majors=list(data.get('preferred_majors') or []),
            required_skills=list(data.get('required_skills') or []),
            bonus_skills=list(data.get('bonus_skills') or []),
            soft_skills=list(data.get('soft_skills') or []),
            certificates=list(data.get('certificates') or []),
            practice_requirements=list(data.get('practice_requirements') or []),
            vertical_growth_path=list(data.get('vertical_growth_path') or []),
            transfer_paths=list(data.get('transfer_paths') or []),
            aliases=list(data.get('aliases') or []),
            source_titles=list(data.get('source_titles') or []),
            sample_count=int(data.get('sample_count') or 0),
            top_cities=list(data.get('top_cities') or []),
            top_industries=list(data.get('top_industries') or []),
            salary_min_monthly=data.get('salary_min_monthly'),
            salary_max_monthly=data.get('salary_max_monthly'),
            evidence_snippets=list(data.get('evidence_snippets') or []),
        )

    def _run_query(self, query: str, parameters: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        with self._driver.session(database=self._database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
