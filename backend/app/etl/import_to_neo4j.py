from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Optional

try:
    from neo4j import GraphDatabase
except Exception as exc:  # pragma: no cover - runtime dependency
    raise ImportError('neo4j package is unavailable in the current environment. Reinstall project dependencies before running the importer.') from exc

from backend.app.core.catalog import JOB_FAMILY_TEMPLATES
from backend.app.core.config import get_settings
from backend.app.schemas.graph import JobGraph, JobGraphEdge
from backend.app.schemas.job import JobRequirementProfile


JAVA_JOB = 'Java开发工程师'
SENIOR_DEV_JOB = '高级开发工程师'
TECH_LEAD_JOB = '技术负责人'
ARCHITECT_JOB = '架构师'

SKILL_MICROSERVICE = '微服务'
SKILL_PERFORMANCE = '性能优化'
SKILL_SYSTEM_DESIGN = '系统设计'
SKILL_ARCH_DESIGN = '架构设计'
SKILL_COLLAB = '跨团队协作'
SKILL_REVIEW = '技术方案评审'
SKILL_DISTRIBUTED = '分布式架构'
SKILL_ABSTRACTION = '系统抽象'
SKILL_ARCH_MINDSET = '架构思维'

ABILITY_INNOVATION = '创新能力'
ABILITY_COMMUNICATION = '沟通能力'
ABILITY_STRESS = '抗压能力'
ABILITY_LEARNING = '学习能力'
ABILITY_EXECUTION = '执行力'

DEFAULT_BASE_DIR = Path('data') / 'knowledge_base'

EDGE_OVERRIDES: dict[tuple[str, str], dict[str, Any]] = {
    (JAVA_JOB, SENIOR_DEV_JOB): {
        'success_rate': 0.86,
        'time_cost': '1-2 years',
        'difficulty': 'medium',
        'required_skills': [SKILL_MICROSERVICE, SKILL_PERFORMANCE, SKILL_SYSTEM_DESIGN],
        'evidence': ['catalog.vertical_growth_path', 'backend engineering growth pattern'],
        'case_count': 58,
        'weight': 0.92,
    },
    (SENIOR_DEV_JOB, TECH_LEAD_JOB): {
        'success_rate': 0.79,
        'time_cost': '1-2 years',
        'difficulty': 'high',
        'required_skills': [SKILL_ARCH_DESIGN, SKILL_COLLAB, SKILL_REVIEW],
        'evidence': ['catalog.vertical_growth_path', 'technical leadership capability evolution'],
        'case_count': 41,
        'weight': 0.85,
    },
    (TECH_LEAD_JOB, ARCHITECT_JOB): {
        'success_rate': 0.72,
        'time_cost': '1-2 years',
        'difficulty': 'high',
        'required_skills': [SKILL_DISTRIBUTED, SKILL_ABSTRACTION, SKILL_ARCH_MINDSET],
        'evidence': ['catalog.vertical_growth_path', 'architecture role transition pattern'],
        'case_count': 28,
        'weight': 0.8,
    },
}

ABILITY_DESCRIPTIONS = {
    ABILITY_INNOVATION: 'Able to propose differentiated solutions and validate them in practice.',
    ABILITY_COMMUNICATION: 'Able to communicate clearly across team and stakeholder scenarios.',
    ABILITY_STRESS: 'Able to deliver steadily under pressure and complexity.',
    ABILITY_LEARNING: 'Able to learn quickly and transfer knowledge into project execution.',
    ABILITY_EXECUTION: 'Able to drive tasks forward and produce deliverable outcomes.',
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
    time_cost = str(override.get('time_cost') or edge.time_cost or ('1-2 years' if relation_type == 'VERTICAL_TO' else '1-3 years'))
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


def build_city_payloads(job_payloads: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    city_counter: Counter[str] = Counter()
    edge_payloads: list[dict[str, Any]] = []
    for job in job_payloads:
        cities = list(job.get('top_cities') or [])
        if not cities:
            continue
        for index, city_name in enumerate(cities, start=1):
            city_counter[city_name] += 1
            edge_payloads.append(
                {
                    'job_name': job['name'],
                    'city_name': city_name,
                    'heat_score': round(max(0.35, 1.0 - (index - 1) * 0.15), 2),
                    'job_count': max(1, int((job.get('sample_count') or 1) / max(len(cities), 1))),
                }
            )
    city_payloads = [{'name': city, 'job_total': count} for city, count in sorted(city_counter.items())]
    return city_payloads, edge_payloads


def build_industry_payloads(job_payloads: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    industry_counter: Counter[str] = Counter()
    edge_payloads: list[dict[str, Any]] = []
    for job in job_payloads:
        industries = list(job.get('top_industries') or [])
        if not industries:
            continue
        market_share = round(1 / len(industries), 2)
        for industry_name in industries:
            industry_counter[industry_name] += 1
            edge_payloads.append(
                {
                    'job_name': job['name'],
                    'industry_name': industry_name,
                    'market_share': market_share,
                }
            )
    industry_payloads = [{'name': industry, 'job_total': count} for industry, count in sorted(industry_counter.items())]
    return industry_payloads, edge_payloads


def ensure_constraints(session) -> None:
    statements = [
        "CREATE CONSTRAINT job_name_unique IF NOT EXISTS FOR (j:Job) REQUIRE j.name IS UNIQUE",
        "CREATE CONSTRAINT skill_name_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE",
        "CREATE CONSTRAINT ability_name_unique IF NOT EXISTS FOR (a:Ability) REQUIRE a.name IS UNIQUE",
        "CREATE CONSTRAINT city_name_unique IF NOT EXISTS FOR (c:City) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT industry_name_unique IF NOT EXISTS FOR (i:Industry) REQUIRE i.name IS UNIQUE",
        "CREATE INDEX job_name_idx IF NOT EXISTS FOR (j:Job) ON (j.name)",
        "CREATE INDEX skill_name_idx IF NOT EXISTS FOR (s:Skill) ON (s.name)",
        "CREATE INDEX ability_name_idx IF NOT EXISTS FOR (a:Ability) ON (a.name)",
        "CREATE INDEX city_name_idx IF NOT EXISTS FOR (c:City) ON (c.name)",
        "CREATE INDEX industry_name_idx IF NOT EXISTS FOR (i:Industry) ON (i.name)",
        "CREATE INDEX transfer_success_rate_idx IF NOT EXISTS FOR ()-[r:TRANSFER_TO]-() ON (r.success_rate)",
    ]
    for statement in statements:
        session.run(statement)


def build_related_to_relationships(session) -> None:
    session.run(
        """
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
    )


def import_graph(uri: str, user: str, password: str, database: str, graph: JobGraph, profiles: dict[str, JobRequirementProfile], drop_existing: bool) -> None:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    job_payloads = build_job_payloads(graph, profiles)
    edge_payloads = [build_edge_payload(edge, profiles) for edge in graph.edges]
    city_payloads, city_edges = build_city_payloads(job_payloads)
    industry_payloads, industry_edges = build_industry_payloads(job_payloads)
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

        ensure_constraints(session)

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

        for city in city_payloads:
            session.run(
                """
                MERGE (c:City {name: $name})
                SET c.job_total = $job_total
                """,
                city,
            )
        for edge in city_edges:
            session.run(
                """
                MATCH (job:Job {name: $job_name})
                MATCH (city:City {name: $city_name})
                MERGE (job)-[r:LOCATED_IN]->(city)
                SET r.heat_score = $heat_score,
                    r.job_count = $job_count
                """,
                edge,
            )

        for industry in industry_payloads:
            session.run(
                """
                MERGE (i:Industry {name: $name})
                SET i.job_total = $job_total
                """,
                industry,
            )
        for edge in industry_edges:
            session.run(
                """
                MATCH (job:Job {name: $job_name})
                MATCH (industry:Industry {name: $industry_name})
                MERGE (job)-[r:BELONGS_TO]->(industry)
                SET r.market_share = $market_share
                """,
                edge,
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

        build_related_to_relationships(session)

    driver.close()


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(description='Import local knowledge graph artifacts into Neo4j.')
    parser.add_argument('--graph-path', default=str(DEFAULT_BASE_DIR / 'job_graph.json'))
    parser.add_argument('--profile-path', default=str(DEFAULT_BASE_DIR / 'job_profiles.json'))
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
