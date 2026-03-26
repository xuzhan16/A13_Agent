from backend.app.repositories.neo4j_knowledge import Neo4jKnowledgeRepository


class _FakeRepo(Neo4jKnowledgeRepository):
    def __init__(self, responses):
        self._responses = list(responses)

    def _run_query(self, query, parameters=None):
        del query, parameters
        return self._responses.pop(0)


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
