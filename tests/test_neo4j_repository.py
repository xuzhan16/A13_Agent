from backend.app.repositories.neo4j_knowledge import Neo4jKnowledgeRepository


class _FakeRepo(Neo4jKnowledgeRepository):
    def __init__(self, responses):
        self._responses = list(responses)
        self.queries = []

    def _run_query(self, query, parameters=None):
        self.queries.append((query, parameters or {}))
        return self._responses.pop(0) if self._responses else []


def test_get_job_graph_maps_records():
    repo = _FakeRepo([
        [
            {
                'id': 'Java',
                'label': 'Java',
                'node_type': 'job_family',
                'sample_count': 10,
                'top_skills': ['Java'],
                'top_cities': ['Shenzhen'],
                'description': 'Backend role',
            }
        ],
        [
            {
                'source': 'Java',
                'target': 'Architect',
                'edge_type': 'vertical',
                'weight': 0.9,
                'reason': 'career path',
                'success_rate': 0.8,
                'time_cost': '2 years',
                'difficulty': 'high',
                'required_skills': ['System Design'],
                'evidence': ['catalog'],
                'case_count': 12,
            }
        ],
    ])

    graph = repo.get_job_graph()

    assert graph.nodes[0].id == 'Java'
    assert graph.edges[0].target == 'Architect'
    assert graph.metadata['source'] == 'neo4j'


def test_find_transfer_paths_builds_structured_result():
    repo = _FakeRepo([
        [
            {
                'jobs': ['Java', 'Senior', 'Architect'],
                'edge_chain': [
                    {
                        'source_job': 'Java',
                        'target_job': 'Senior',
                        'relation_type': 'VERTICAL_TO',
                        'success_rate': 0.86,
                        'time_cost': '1-2 years',
                        'difficulty': 'medium',
                        'required_skills': ['Microservices'],
                        'evidence': ['catalog'],
                        'case_count': 12,
                        'weight': 0.9,
                    },
                    {
                        'source_job': 'Senior',
                        'target_job': 'Architect',
                        'relation_type': 'VERTICAL_TO',
                        'success_rate': 0.72,
                        'time_cost': '1-2 years',
                        'difficulty': 'high',
                        'required_skills': ['System Design'],
                        'evidence': ['report'],
                        'case_count': 8,
                        'weight': 0.8,
                    },
                ],
                'steps': 2,
            }
        ]
    ])

    results = repo.find_transfer_paths('Java', 'Architect', max_steps=3)

    assert len(results) == 1
    assert results[0].jobs == ['Java', 'Senior', 'Architect']
    assert results[0].steps == 2
    assert results[0].difficulty == 'high'


def test_get_job_recommendations_enriches_evidence_snippets():
    repo = _FakeRepo([
        [
            {
                'job': {
                    'name': 'Backend Engineer',
                    'description': 'Backend role',
                    'required_skills': ['Java', 'SQL'],
                    'sample_count': 18,
                    'evidence_snippets': ['existing evidence'],
                },
                'common_skill_count': 3,
                'shared_skills': ['Java', 'Spring Boot', 'MySQL'],
            }
        ]
    ])

    recommendations = repo.get_job_recommendations('Java Engineer', limit=5)

    assert len(recommendations) == 1
    assert recommendations[0].job_family == 'Backend Engineer'
    assert any('Shared skills:' in item for item in recommendations[0].evidence_snippets)
    assert any('Skill overlap count:' in item for item in recommendations[0].evidence_snippets)


def test_get_job_entry_points_orders_shorter_path_first():
    repo = _FakeRepo([
        [
            {
                'jobs': ['Support', 'Architect'],
                'edge_chain': [
                    {
                        'source_job': 'Support',
                        'target_job': 'Architect',
                        'relation_type': 'TRANSFER_TO',
                        'success_rate': 0.55,
                        'time_cost': '3 years',
                        'difficulty': 'high',
                        'required_skills': ['Architecture'],
                        'evidence': ['report'],
                        'case_count': 4,
                        'weight': 0.5,
                    }
                ],
                'steps': 1,
            },
            {
                'jobs': ['QA', 'Senior QA', 'Architect'],
                'edge_chain': [
                    {
                        'source_job': 'QA',
                        'target_job': 'Senior QA',
                        'relation_type': 'VERTICAL_TO',
                        'success_rate': 0.7,
                        'time_cost': '1 year',
                        'difficulty': 'medium',
                        'required_skills': ['Automation'],
                        'evidence': ['catalog'],
                        'case_count': 5,
                        'weight': 0.6,
                    },
                    {
                        'source_job': 'Senior QA',
                        'target_job': 'Architect',
                        'relation_type': 'TRANSFER_TO',
                        'success_rate': 0.4,
                        'time_cost': '2 years',
                        'difficulty': 'high',
                        'required_skills': ['Architecture'],
                        'evidence': ['report'],
                        'case_count': 3,
                        'weight': 0.4,
                    },
                ],
                'steps': 2,
            },
        ]
    ])

    results = repo.get_job_entry_points('Architect', max_steps=4)

    assert results[0].jobs == ['Support', 'Architect']
    assert results[1].jobs == ['QA', 'Senior QA', 'Architect']


def test_get_job_clusters_merges_overlap_pairs():
    repo = _FakeRepo([
        [
            {'source': 'Java', 'target': 'Backend', 'common_skills': 4},
            {'source': 'Backend', 'target': 'Architect', 'common_skills': 3},
        ],
        [
            {'j': {'name': 'Java', 'description': 'role'}},
            {'j': {'name': 'Backend', 'description': 'role'}},
            {'j': {'name': 'Architect', 'description': 'role'}},
            {'j': {'name': 'Tester', 'description': 'role'}},
        ],
    ])

    clusters = repo.get_job_clusters()

    assert any(set(items) == {'Java', 'Backend', 'Architect'} for items in clusters.values())
    assert any(set(items) == {'Tester'} for items in clusters.values())


def test_get_job_influence_ranking_returns_float_scores():
    repo = _FakeRepo([
        [
            {'job_name': 'Architect', 'influence_score': 7},
            {'job_name': 'Java', 'influence_score': 5.0},
        ]
    ])

    ranking = repo.get_job_influence_ranking()

    assert ranking == [('Architect', 7.0), ('Java', 5.0)]


def test_build_job_relationships_executes_related_to_query():
    repo = _FakeRepo([[]])

    repo.build_job_relationships()

    assert 'RELATED_TO' in repo.queries[0][0]
