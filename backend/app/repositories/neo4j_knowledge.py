from __future__ import annotations

from typing import Any, Optional

try:
    from neo4j import GraphDatabase
except Exception:  # pragma: no cover - optional dependency at runtime
    GraphDatabase = None

from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.graph import GraphEntityDetail, GraphRelationPreview, JobGraph, JobGraphEdge, JobGraphNode
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
               coalesce(j.top_industries, []) AS top_industries,
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

    def get_job_recommendations(self, job: str, limit: int = 5) -> list[JobRequirementProfile]:
        query = """
        MATCH (source:Job {name: $job})-[:REQUIRES]->(skill:Skill)<-[:REQUIRES]-(target:Job)
        WHERE source <> target AND coalesce(target.node_type, 'job_family') = 'job_family'
        WITH target, count(DISTINCT skill) AS common_skill_count, collect(DISTINCT skill.name)[0..8] AS shared_skills
        ORDER BY common_skill_count DESC, coalesce(target.sample_count, 0) DESC, target.name ASC
        LIMIT $limit
        RETURN target AS job, common_skill_count, shared_skills
        """
        profiles: list[JobRequirementProfile] = []
        for record in self._run_query(query, {'job': job, 'limit': limit}):
            profile = self._profile_from_props(record['job'])
            profile.evidence_snippets = self._unique([
                *profile.evidence_snippets,
                f"Shared skills: {', '.join(record.get('shared_skills', []))}",
                f"Skill overlap count: {record.get('common_skill_count', 0)}",
            ])
            profiles.append(profile)
        return profiles

    def get_job_entry_points(self, target_job: str, max_steps: int = 5) -> list[TransferPathResult]:
        hops = max(1, min(int(max_steps), 8))
        query = f"""
        MATCH path = (start:Job)-[:TRANSFER_TO|VERTICAL_TO*1..{hops}]->(end:Job {{name: $target_job}})
        WHERE start.name <> end.name
          AND all(node IN nodes(path) WHERE single(other IN nodes(path) WHERE other = node))
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
        records = self._run_query(query, {'target_job': target_job})
        results = [self._path_result_from_record(record) for record in records]
        return sorted(results, key=lambda item: (item.steps, -item.cumulative_success_rate, item.jobs[0] if item.jobs else ''))

    def get_job_clusters(self) -> dict[str, list[str]]:
        query = """
        MATCH (j1:Job)-[:REQUIRES]->(s:Skill)<-[:REQUIRES]-(j2:Job)
        WHERE j1.name < j2.name
          AND coalesce(j1.node_type, 'job_family') = 'job_family'
          AND coalesce(j2.node_type, 'job_family') = 'job_family'
        WITH j1.name AS source, j2.name AS target, count(DISTINCT s) AS common_skills
        WHERE common_skills >= 2
        RETURN source, target, common_skills
        ORDER BY common_skills DESC, source ASC, target ASC
        """
        records = self._run_query(query)
        jobs = [profile.job_family for profile in self.list_job_families()]
        parents = {job: job for job in jobs}

        def find(node: str) -> str:
            while parents[node] != node:
                parents[node] = parents[parents[node]]
                node = parents[node]
            return node

        def union(left: str, right: str) -> None:
            left_root = find(left)
            right_root = find(right)
            if left_root != right_root:
                parents[right_root] = left_root

        for record in records:
            union(record['source'], record['target'])

        clusters: dict[str, list[str]] = {}
        for job in jobs:
            root = find(job)
            clusters.setdefault(root, []).append(job)

        normalized: dict[str, list[str]] = {}
        for index, members in enumerate(sorted(clusters.values(), key=lambda item: (-len(item), item[0])) , start=1):
            normalized[f'cluster_{index}'] = sorted(members)
        return normalized

    def get_job_influence_ranking(self) -> list[tuple[str, float]]:
        query = """
        MATCH (j:Job)
        WHERE coalesce(j.node_type, 'job_family') = 'job_family'
        OPTIONAL MATCH (j)-[:VERTICAL_TO|TRANSFER_TO]->(out_neighbor:Job)
        WITH j, count(DISTINCT out_neighbor) AS out_degree
        OPTIONAL MATCH (j)<-[:VERTICAL_TO|TRANSFER_TO]-(in_neighbor:Job)
        WITH j.name AS job_name, toFloat(count(DISTINCT in_neighbor) * 2 + out_degree) AS influence_score
        ORDER BY influence_score DESC, job_name ASC
        RETURN job_name, influence_score
        """
        return [(record['job_name'], float(record['influence_score'])) for record in self._run_query(query)]

    def build_job_relationships(self) -> None:
        query = """
        MATCH (j1:Job)-[:REQUIRES]->(s:Skill)<-[:REQUIRES]-(j2:Job)
        WHERE j1.name < j2.name
          AND coalesce(j1.node_type, 'job_family') = 'job_family'
          AND coalesce(j2.node_type, 'job_family') = 'job_family'
        WITH j1, j2, count(DISTINCT s) AS common_skills, collect(DISTINCT s.name)[0..8] AS shared_skills
        WHERE common_skills >= 2
        MERGE (j1)-[r:RELATED_TO]->(j2)
        SET r.similarity_score = toFloat(common_skills),
            r.shared_skills = shared_skills,
            r.reason = 'Derived from shared skill lineage'
        """
        self._run_query(query)

    def get_graph_entity_detail(self, entity_id: str, node_type: str = 'job_family') -> GraphEntityDetail:
        normalized_type = str(node_type or 'job_family').lower()
        normalized_id = entity_id.split('skill::', 1)[-1] if entity_id.startswith('skill::') else entity_id
        if normalized_type == 'skill':
            return self._get_skill_detail(normalized_id)
        if normalized_type == 'ability':
            return self._get_ability_detail(normalized_id)
        return self._get_job_detail(normalized_id)

    def _get_job_detail(self, job_name: str) -> GraphEntityDetail:
        query = """
        MATCH (j:Job {name: $job_name})
        CALL {
            WITH j
            OPTIONAL MATCH (j)-[:LOCATED_IN]->(c:City)
            RETURN collect(DISTINCT c.name) AS cities
        }
        CALL {
            WITH j
            OPTIONAL MATCH (j)-[:BELONGS_TO]->(i:Industry)
            RETURN collect(DISTINCT i.name) AS industries
        }
        CALL {
            WITH j
            OPTIONAL MATCH (j)-[out:TRANSFER_TO|VERTICAL_TO]->(next:Job)
            WITH collect(DISTINCT CASE WHEN next IS NULL THEN NULL ELSE {
                target_id: next.name,
                label: coalesce(next.label, next.name),
                node_type: coalesce(next.node_type, 'job_family'),
                relation_type: type(out),
                success_rate: coalesce(out.success_rate, 0.0),
                time_cost: coalesce(out.time_cost, ''),
                difficulty: coalesce(out.difficulty, 'medium'),
                required_skills: coalesce(out.required_skills, []),
                evidence: coalesce(out.evidence, [])
            } END) AS items
            RETURN [item IN items WHERE item IS NOT NULL] AS outgoing_relations
        }
        CALL {
            WITH j
            OPTIONAL MATCH (prev:Job)-[inc:TRANSFER_TO|VERTICAL_TO]->(j)
            WITH collect(DISTINCT CASE WHEN prev IS NULL THEN NULL ELSE {
                target_id: prev.name,
                label: coalesce(prev.label, prev.name),
                node_type: coalesce(prev.node_type, 'job_family'),
                relation_type: type(inc),
                success_rate: coalesce(inc.success_rate, 0.0),
                time_cost: coalesce(inc.time_cost, ''),
                difficulty: coalesce(inc.difficulty, 'medium'),
                required_skills: coalesce(inc.required_skills, []),
                evidence: coalesce(inc.evidence, [])
            } END) AS items,
            count(DISTINCT prev) AS in_degree
            RETURN [item IN items WHERE item IS NOT NULL] AS incoming_relations, in_degree
        }
        CALL {
            WITH j
            OPTIONAL MATCH (j)-[:VERTICAL_TO|TRANSFER_TO]->(next:Job)
            RETURN count(DISTINCT next) AS out_degree
        }
        RETURN j AS job,
               cities,
               industries,
               outgoing_relations,
               incoming_relations,
               toFloat(in_degree * 2 + out_degree) AS influence_score
        LIMIT 1
        """
        records = self._run_query(query, {'job_name': job_name})
        if not records:
            return GraphEntityDetail(entity_id=job_name, label=job_name, node_type='job_family')

        record = records[0]
        job_props = dict(record['job'])
        profile = self._profile_from_props(record['job'])
        recommended_jobs = [item.job_family for item in self.get_job_recommendations(job_name, limit=5)]
        entry_paths = [item.jobs for item in self.get_job_entry_points(job_name, max_steps=3)[:3]]
        return GraphEntityDetail(
            entity_id=job_name,
            label=job_props.get('label', job_name),
            node_type=job_props.get('node_type', 'job_family'),
            description=job_props.get('description', ''),
            sample_count=int(job_props.get('sample_count') or 0),
            top_skills=list(job_props.get('top_skills') or profile.required_skills[:6]),
            top_cities=list(job_props.get('top_cities') or []),
            top_industries=list(job_props.get('top_industries') or []),
            cities=self._unique(record.get('cities') or []),
            industries=self._unique(record.get('industries') or []),
            required_skills=profile.required_skills,
            bonus_skills=profile.bonus_skills,
            soft_skills=profile.soft_skills,
            certificates=profile.certificates,
            practice_requirements=profile.practice_requirements,
            vertical_growth_path=profile.vertical_growth_path,
            transfer_paths=profile.transfer_paths,
            recommended_jobs=recommended_jobs,
            entry_paths=entry_paths,
            incoming_relations=self._relation_previews(record.get('incoming_relations') or []),
            outgoing_relations=self._relation_previews(record.get('outgoing_relations') or []),
            salary_min_monthly=profile.salary_min_monthly,
            salary_max_monthly=profile.salary_max_monthly,
            influence_score=float(record.get('influence_score') or 0),
            evidence_snippets=profile.evidence_snippets,
        )

    def _get_skill_detail(self, skill_name: str) -> GraphEntityDetail:
        query = """
        MATCH (s:Skill {name: $skill_name})
        OPTIONAL MATCH (j:Job)-[:REQUIRES]->(s)
        RETURN s AS skill, collect(DISTINCT j.name)[0..10] AS linked_jobs
        LIMIT 1
        """
        records = self._run_query(query, {'skill_name': skill_name})
        if not records:
            return GraphEntityDetail(entity_id=skill_name, label=skill_name, node_type='skill')
        record = records[0]
        skill_props = dict(record['skill'])
        return GraphEntityDetail(
            entity_id=skill_name,
            label=skill_props.get('name', skill_name),
            node_type='skill',
            description=skill_props.get('description', ''),
            linked_jobs=self._unique(record.get('linked_jobs') or []),
            recommended_jobs=self._unique(record.get('linked_jobs') or [])[:5],
            category=str(skill_props.get('category') or ''),
            difficulty=str(skill_props.get('difficulty') or ''),
            market_demand=float(skill_props.get('market_demand') or 0),
            trend=str(skill_props.get('trend') or ''),
        )

    def _get_ability_detail(self, ability_name: str) -> GraphEntityDetail:
        query = """
        MATCH (a:Ability {name: $ability_name})
        OPTIONAL MATCH (j:Job)-[:DEPENDS_ON]->(a)
        RETURN a AS ability, collect(DISTINCT j.name)[0..10] AS linked_jobs
        LIMIT 1
        """
        records = self._run_query(query, {'ability_name': ability_name})
        if not records:
            return GraphEntityDetail(entity_id=ability_name, label=ability_name, node_type='ability')
        record = records[0]
        ability_props = dict(record['ability'])
        return GraphEntityDetail(
            entity_id=ability_name,
            label=ability_props.get('name', ability_name),
            node_type='ability',
            description=ability_props.get('description', ''),
            linked_jobs=self._unique(record.get('linked_jobs') or []),
            recommended_jobs=self._unique(record.get('linked_jobs') or [])[:5],
            difficulty=str(ability_props.get('level') or ''),
        )

    @staticmethod
    def _relation_previews(records: list[dict[str, Any]]) -> list[GraphRelationPreview]:
        previews: list[GraphRelationPreview] = []
        for item in records:
            if not item or not item.get('target_id'):
                continue
            previews.append(
                GraphRelationPreview(
                    target_id=item.get('target_id', ''),
                    label=item.get('label', item.get('target_id', '')),
                    node_type=item.get('node_type', 'job_family'),
                    relation_type=item.get('relation_type', ''),
                    success_rate=float(item.get('success_rate') or 0),
                    time_cost=str(item.get('time_cost') or ''),
                    difficulty=str(item.get('difficulty') or 'medium'),
                    required_skills=list(item.get('required_skills') or []),
                    evidence=list(item.get('evidence') or []),
                )
            )
        return previews

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
