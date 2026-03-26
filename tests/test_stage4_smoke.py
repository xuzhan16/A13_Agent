import os

os.environ['ENABLE_LLM'] = 'false'

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


def test_demo_page_loads() -> None:
    response = client.get('/')
    assert response.status_code == 200
    assert 'page-shell' in response.text
    assert 'softSkillOverview' in response.text
    assert 'trendPanel' in response.text


def test_export_markdown_endpoint() -> None:
    response = client.post('/api/v1/planning/report/export-markdown', json=SAMPLE_REQUEST)
    assert response.status_code == 200
    assert 'attachment;' in response.headers.get('content-disposition', '').lower()
    assert '# ' in response.text
    assert 'trend-snapshot/2026.03' in response.text


def test_report_contains_evidence_trace_soft_skills_and_trend() -> None:
    response = client.post('/api/v1/planning/report', json=SAMPLE_REQUEST)
    assert response.status_code == 200
    payload = response.json()
    top_match = payload['match_results'][0]

    assert 'evidence_trace' in top_match
    assert top_match['evidence_trace']['final_score']['formula']
    assert len(top_match['evidence_trace']['dimensions']) == 4
    assert all(item['indicators'] for item in top_match['evidence_trace']['dimensions'])
    assert len(top_match['evidence_trace']['evidences']) >= 1

    soft_skills = payload['student_profile']['soft_skill_assessments']
    assert len(soft_skills) == 5
    assert any(item['skill_code'] == 'communication' for item in soft_skills)
    assert any(item['skill_code'] == 'learning_agility' for item in soft_skills)

    industry_trend = payload['report']['industry_trend']
    assert industry_trend['snapshot_version'] == 'trend-snapshot/2026.03'
    assert industry_trend['role_heat']
    assert industry_trend['missing_skill_trends']
    assert industry_trend['personalized_advice']

    literacy_dimension = next(item for item in top_match['dimension_scores'] if item['dimension_code'] == 'professional_literacy')
    indicator_codes = [item['indicator_code'] for item in literacy_dimension['indicators']]
    assert 'literacy.communication' in indicator_codes
    assert 'literacy.execution' in indicator_codes
