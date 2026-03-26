from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from neo4j import GraphDatabase
except Exception as exc:  # pragma: no cover - runtime dependency
    raise ImportError('neo4j package is unavailable in the current environment. Reinstall project dependencies before running the importer.') from exc

from backend.app.core.catalog import JOB_FAMILY_TEMPLATES
from backend.app.core.config import get_settings
from backend.app.schemas.graph import JobGraph, JobGraphEdge
from backend.app.schemas.job import JobRequirementProfile


EDGE_OVERRIDES: dict[tuple[str, str], dict[str, Any]] = {
    ('Java开发工程师', '高级开发工程师'): {
        'success_rate': 0.86,
        'time_cost': '1-2年',
        'difficulty': 'medium',
        'required_skills': ['微服务', '性能优化', '系统设计'],
        'evidence': ['catalog.vertical_growth_path', '后端工程经验积累规律'],
        'case_count': 58,
        'weight': 0.92,
    },
    ('高级开发工程师', '技术负责人'): {
        'success_rate': 0.79,
        'time_cost': '1-2年',
        'difficulty': 'high',
        'required_skills': ['架构设计', '跨团队协作', '技术方案评审'],
        'evidence': ['catalog.vertical_growth_path', '团队技术主导能力演进'],
        'case_count': 41,
        'weight': 0.85,
    },
    ('技术负责人', '架构师'): {
        'success_rate': 0.72,
        'time_cost': '1-2年',
        'difficulty': 'high',
        'required_skills': ['分布式架构', '系统抽象', '架构思维'],
        'evidence': ['catalog.vertical_growth_path', '架构岗位能力迁移要求'],
        'case_count': 28,
        'weight': 0.8,
    },
}

ABILITY_DESCRIPTIONS = {
    '创新能力': '能够提出新的解决方案并完成落地验证。',
    '沟通能力': '能够在团队协作和跨角色场景中清晰表达。',
    '抗压能力': '能在时间压力与复杂任务下稳定交付。',
    '学习能力': '能够快速掌握新知识并迁移到实践。',
    '执行力': '能够按计划推进并形成可验收交付物。',
}


def load_profiles(profile_path: Path) -> dict[str, JobRequirementProfile]:
    payload = json.loads(profile_path.read_text(encoding='utf-8'))
    return {item['job_family']: JobRequirementProfile(**item) for item in payload}


def load_graph(graph_path: Path) -> JobGraph:
    payload = json.loads(graph_path.read_text(encoding='utf-8'))
    return JobGraph(**payload)


def default_success_rate(edge_type: str, weight: float) -> float:
    normalized_weight = weight or (1.0 if edge_type == 'vertical' else 0.45)
    base = 0.68 if edge_type == 'vertical' else 0.52
    return round(min(0.95, base + normalized_weight * 0.18), 2)


def infer_required_skills(source: Optional[JobRequirementProfile], target: Optional[JobRequirementProfile]) -> list[str]:
    if target is None:
        return []
    source_skills = set((source.required_skills if source else []) + (source.bonus_skills if source else []))
    target_skills = list(dict.fromkeys(target.required_skills + target.bonus_skills))
    return [skill for skill in target_skills if skill not in source_skills][:4]


def infer_difficulty(required_skills: list[str], relation_type: str) -> str:
    if relation_type == 'VERTICAL_TO' and len(required_skills) >= 3:
        return 'high'
    if len(required_skills) >= 4:
        return 'high'
    if len(required_skills) >= 2:
        return 'medium'
    return 'low'


def infer_case_count(source: Optional[JobRequirementProfile], target: Optional[JobRequirementProfile]) -> int:
    values = [value for value in [getattr(source, 'sample_count', 0), getattr(target, 'sample_count', 0)] if value > 0]
    return int(min(values) / 10) if values else 12


def build_job_payloads(graph: JobGraph, profiles: dict[str, JobRequirementProfile]) -> list[dict[str, Any]]:
    template_map = {item.job_family: item for item in JOB_FAMILY_TEMPLATES}
    jobs: list[dict[str, Any]] = []
    for node in graph.nodes:
        profile = profiles.get(node.id)
        template = template_map.get(node.id)
        jobs.append(
            {
                'name': node.id,
                'label': node.label,
                'node_type': node.node_type,
                'description': getattr(profile, 'description', '') or getattr(template, 'description', '') or f'Career stage for {node.label}',
                'sample_count': node.sample_count,
                'top_skills': list(node.top_skills),
                'top_cities': list(node.top_cities),
                'preferred_majors': list(getattr(profile, 'preferred_majors', []) or getattr(template, 'preferred_majors', []) or []),
                'required_skills': list(getattr(profile, 'required_skills', []) or getattr(template, 'required_skills', []) or []),
                'bonus_skills': list(getattr(profile, 'bonus_skills', []) or getattr(template, 'bonus_skills', []) or []),
                'soft_skills': list(getattr(profile, 'soft_skills', []) or getattr(template, 'soft_skills', []) or []),
                'certificates': list(getattr(profile, 'certificates', []) or getattr(template, 'certificates', []) or []),
                'practice_requirements': list(getattr(profile, 'practice_requirements', []) or getattr(template, 'practice_requirements', []) or []),
                'vertical_growth_path': list(getattr(profile, 'vertical_growth_path', []) or getattr(template, 'vertical_growth_path', []) or []),
                'transfer_paths': list(getattr(profile, 'transfer_paths', []) or getattr(template, 'transfer_paths', []) or []),
                'aliases': list(getattr(profile, 'aliases', []) or getattr(template, 'aliases', []) or []),
                'source_titles': list(getattr(profile, 'source_titles', []) or []),
                'top_industries': list(getattr(profile, 'top_industries', []) or []),
                'salary_min_monthly': getattr(profile, 'salary_min_monthly', None),
                'salary_max_monthly': getattr(profile, 'salary_max_monthly', None),
                'evidence_snippets': list(getattr(profile, 'evidence_snippets', []) or []),
            }
        )
    return jobs


def build_edge_payload(edge: JobGraphEdge, profiles: dict[str, JobRequirementProfile]) -> dict[str, Any]:
    source_profile = profiles.get(edge.source)
    target_profile = profiles.get(edge.target)
    relation_type = 'VERTICAL_TO' if edge.edge_type == 'vertical' else 'TRANSFER_TO'
    override = EDGE_OVERRIDES.get((edge.source, edge.target), {})
    required_skills = list(override.get('required_skills') or edge.required_skills or infer_required_skills(source_profile, target_profile))
    success_rate = float(override.get('success_rate') or edge.success_rate or default_success_rate(edge.edge_type, edge.weight))
    time_cost = str(override.get('time_cost') or edge.time_cost or ('1-2年' if relation_type == 'VERTICAL_TO' else '1-3年'))
    evidence = list(override.get('evidence') or edge.evidence or [edge.reason or 'graph import', 'job_graph.json'])
    difficulty = str(override.get('difficulty') or edge.difficulty or infer_difficulty(required_skills, relation_type))
    case_count = int(override.get('case_count') or edge.case_count or infer_case_count(source_profile, target_profile))
    weight = float(override.get('weight') or edge.weight or 0.0)
    return {
        'source': edge.source,
        'target': edge.target,
        'relation_type': relation_type,
        'weight': weight,
        'reason': edge.reason,
        'success_rate': success_rate,
        'time_cost': time_cost,
        'difficulty': difficulty,
        'required_skills': required_skills,
        'evidence': evidence,
        'case_count': case_count,
    }


def import_graph(uri: str, user: str, password: str, database: str, graph: JobGraph, profiles: dict[str, JobRequirementProfile], drop_existing: bool) -> None:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    job_payloads = build_job_payloads(graph, profiles)
    edge_payloads = [build_edge_payload(edge, profiles) for edge in graph.edges]
    skill_payloads: dict[str, dict[str, Any]] = {}
    ability_payloads: dict[str, dict[str, Any]] = {}

    for job in job_payloads:
        for idx, skill in enumerate(job['required_skills']):
            skill_payloads.setdefault(skill, {
                'name': skill,
                'category': 'required',
                'difficulty': 'medium',
                'market_demand': round(0.7 + min(idx, 4) * 0.03, 2),
                'trend': 'stable',
            })
        for idx, skill in enumerate(job['bonus_skills']):
            skill_payloads.setdefault(skill, {
                'name': skill,
                'category': 'bonus',
                'difficulty': 'medium',
                'market_demand': round(0.55 + min(idx, 4) * 0.03, 2),
                'trend': 'growing',
            })
        for ability in job['soft_skills']:
            ability_payloads.setdefault(ability, {
                'name': ability,
                'level': 'core',
                'description': ABILITY_DESCRIPTIONS.get(ability, f'Capability requirement for {ability}'),
            })

    with driver.session(database=database) as session:
        if drop_existing:
            session.run('MATCH (n) DETACH DELETE n')

        for job in job_payloads:
            session.run(
                """
                MERGE (j:Job {name: $name})
                SET j += $payload
                """,
                {'name': job['name'], 'payload': job},
            )
            for skill in job['required_skills']:
                session.run(
                    """
                    MERGE (s:Skill {name: $skill_name})
                    SET s += $skill_payload
                    WITH s
                    MATCH (j:Job {name: $job_name})
                    MERGE (j)-[r:REQUIRES {requirement_type: 'required'}]->(s)
                    SET r.importance = $importance
                    """,
                    {
                        'job_name': job['name'],
                        'skill_name': skill,
                        'skill_payload': skill_payloads[skill],
                        'importance': 1.0,
                    },
                )
            for skill in job['bonus_skills']:
                session.run(
                    """
                    MERGE (s:Skill {name: $skill_name})
                    SET s += $skill_payload
                    WITH s
                    MATCH (j:Job {name: $job_name})
                    MERGE (j)-[r:REQUIRES {requirement_type: 'bonus'}]->(s)
                    SET r.importance = $importance
                    """,
                    {
                        'job_name': job['name'],
                        'skill_name': skill,
                        'skill_payload': skill_payloads[skill],
                        'importance': 0.6,
                    },
                )
            for ability in job['soft_skills']:
                session.run(
                    """
                    MERGE (a:Ability {name: $ability_name})
                    SET a += $ability_payload
                    WITH a
                    MATCH (j:Job {name: $job_name})
                    MERGE (j)-[r:DEPENDS_ON]->(a)
                    SET r.dependency_strength = $strength
                    """,
                    {
                        'job_name': job['name'],
                        'ability_name': ability,
                        'ability_payload': ability_payloads[ability],
                        'strength': 0.8,
                    },
                )

        for edge in edge_payloads:
            session.run(
                f"""
                MATCH (source:Job {{name: $source}})
                MATCH (target:Job {{name: $target}})
                MERGE (source)-[rel:{edge['relation_type']}]->(target)
                SET rel.weight = $weight,
                    rel.reason = $reason,
                    rel.success_rate = $success_rate,
                    rel.time_cost = $time_cost,
                    rel.difficulty = $difficulty,
                    rel.required_skills = $required_skills,
                    rel.evidence = $evidence,
                    rel.case_count = $case_count
                """,
                edge,
            )

    driver.close()


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(description='Import local knowledge graph artifacts into Neo4j.')
    parser.add_argument('--graph-path', default=str(Path(settings.knowledge_base_dir) / 'job_graph.json'))
    parser.add_argument('--profile-path', default=str(Path(settings.knowledge_base_dir) / 'job_profiles.json'))
    parser.add_argument('--uri', default=settings.neo4j_uri)
    parser.add_argument('--user', default=settings.neo4j_user)
    parser.add_argument('--password', default=settings.neo4j_password)
    parser.add_argument('--database', default=settings.neo4j_database)
    parser.add_argument('--drop-existing', action='store_true')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    graph = load_graph(Path(args.graph_path))
    profiles = load_profiles(Path(args.profile_path))
    import_graph(
        uri=args.uri,
        user=args.user,
        password=args.password,
        database=args.database,
        graph=graph,
        profiles=profiles,
        drop_existing=args.drop_existing,
    )
    print('Neo4j import completed.')


if __name__ == '__main__':
    main()
