from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


SAMPLE_REQUEST = {
    'intake': {
        'basic_info': {
            'name': '李华',
            'school': '某大学',
            'major': '软件工程',
            'degree': '本科',
            'graduation_year': 2026,
        },
        'preference': {
            'target_roles': ['Java开发工程师', '软件测试工程师'],
            'target_cities': ['深圳'],
            'desired_industries': ['互联网', '计算机软件'],
            'prefer_stability': False,
            'prefer_innovation': True,
        },
        'resume_text': '熟悉Java、Spring Boot、MySQL、Redis，完成过校园管理系统开发。',
        'self_description': '学习能力强，善于沟通。',
        'manual_skills': ['Java', 'Spring Boot', 'MySQL', 'Redis'],
        'project_experiences': ['校园管理系统：负责后端接口和权限模块开发。'],
        'internship_experiences': ['参与企业管理系统开发与测试联调。'],
        'campus_experiences': ['技术社团负责人。'],
        'certificates': ['英语四级'],
        'follow_up_answers': [],
    },
    'preferred_job_family': 'Java开发工程师',
    'top_k_matches': 3,
    'max_follow_up_questions': 4,
}


def test_demo_page_loads() -> None:
    response = client.get('/')
    assert response.status_code == 200
    assert 'page-shell' in response.text
    assert '/static/app.js' in response.text


def test_export_markdown_endpoint() -> None:
    response = client.post('/api/v1/planning/report/export-markdown', json=SAMPLE_REQUEST)
    assert response.status_code == 200
    assert 'attachment;' in response.headers.get('content-disposition', '').lower()
    assert '# 大学生职业生涯发展报告' in response.text
