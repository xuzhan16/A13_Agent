import os

os.environ['ENABLE_LLM'] = 'false'
os.environ['KNOWLEDGE_SOURCE'] = 'file'

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)

SAMPLE_REQUEST = {
    'intake': {
        'basic_info': {
            'name': 'Li Hua',
            'school': 'Demo University',
            'major': 'Software Engineering',
            'degree': 'Bachelor',
            'graduation_year': 2026,
        },
        'preference': {
            'target_roles': ['Java?????', '???????'],
            'target_cities': ['??'],
            'desired_industries': ['???', '?????'],
            'prefer_stability': False,
            'prefer_innovation': True,
        },
        'resume_text': 'Java Spring Boot MySQL Redis cache optimization from 280ms to 120ms, with alignment, presentation and launch support.',
        'self_description': 'Fast learner, good communication, can push tasks in a team.',
        'manual_skills': ['Java', 'Spring Boot', 'MySQL', 'Redis'],
        'project_experiences': ['Campus management system: owned backend API, schema design and Redis cache optimization from 280ms to 120ms.'],
        'internship_experiences': ['Joined enterprise system development, requirement communication, bug follow-up and launch support.'],
        'campus_experiences': ['Tech club leader, organized training camp and project demo sessions.'],
        'certificates': ['CET-4'],
        'follow_up_answers': [],
    },
    'preferred_job_family': 'Java?????',
    'top_k_matches': 3,
    'max_follow_up_questions': 4,
}


def test_personalized_subgraph_endpoint() -> None:
    report_response = client.post('/api/v1/planning/report', json=SAMPLE_REQUEST)
    assert report_response.status_code == 200
    report_payload = report_response.json()

    top_match = report_payload['match_results'][0]
    top_path = report_payload['path_options'][0]
    graph_request = {
        'focus_job': top_match['job_family'],
        'target_job': top_path['target_role'] or None,
        'recommended_jobs': [item['job_family'] for item in report_payload['match_results'][:3]],
        'student_skills': report_payload['student_profile']['hard_skills'],
        'missing_skills': top_match['missing_skills'],
        'max_paths': 3,
    }

    graph_response = client.post('/api/v1/planning/graph/personalized-subgraph', json=graph_request)
    assert graph_response.status_code == 200
    graph_payload = graph_response.json()

    assert graph_payload['summary']['focus_job'] == graph_request['focus_job']
    assert graph_payload['summary']['recommended_jobs']
    assert any(node['id'].startswith('skill::') for node in graph_payload['nodes'])
    assert any(edge.get('highlight') == 'selected_path' for edge in graph_payload['edges'])
    assert graph_payload['metadata']['scope'] == 'personalized_subgraph'
