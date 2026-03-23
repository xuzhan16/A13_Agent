from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_follow_up_questions_endpoint() -> None:
    payload = {
        'intake': {
            'basic_info': {
                'name': '测试同学',
                'school': '某大学',
                'major': '软件工程',
                'degree': '本科',
                'graduation_year': 2026,
            },
            'preference': {
                'target_roles': [],
                'target_cities': [],
                'desired_industries': ['互联网'],
                'prefer_stability': False,
                'prefer_innovation': True,
            },
            'resume_text': '熟悉 Java、Spring Boot，做过课程项目。',
            'self_description': '学习能力强。',
            'manual_skills': ['Java', 'Spring Boot'],
            'project_experiences': [],
            'internship_experiences': [],
            'campus_experiences': [],
            'certificates': [],
            'follow_up_answers': [],
        },
        'top_k_matches': 3,
        'max_questions': 4,
    }
    response = client.post('/api/v1/planning/follow-up-questions', json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body['questions']
    assert body['metadata']['knowledge_base_source']


def test_resume_parse_text_file() -> None:
    files = {
        'file': (
            'resume.txt',
            '教育经历\n某大学 软件工程\n项目经历\n校园管理系统'.encode('utf-8'),
            'text/plain',
        )
    }
    response = client.post('/api/v1/planning/resume/parse', files=files)
    assert response.status_code == 200
    body = response.json()
    assert body['parsed_success'] is True
    assert body['char_count'] > 0
    assert 'education' in body['section_hints']
