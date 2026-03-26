import os

os.environ['ENABLE_LLM'] = 'false'

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.resume_parser import ResumeParserService
import backend.app.services.resume_parser as resume_parser_module


client = TestClient(app)


def parse_resume_text(file_name: str, text: str) -> dict:
    response = client.post(
        '/api/v1/planning/resume/parse',
        files={'file': (file_name, text.encode('utf-8'), 'text/plain')},
    )
    assert response.status_code == 200
    return response.json()


def test_resume_parse_extracts_basic_info_and_skills() -> None:
    payload = parse_resume_text(
        'resume.txt',
        '''张三
某理工大学 软件工程 本科 2026届
专业技能
Java、Spring Boot、MySQL、Redis、Git、Linux
项目经历
校园二手交易平台
2025.03-2025.06
负责用户、商品、订单模块开发，使用 Spring Boot + MySQL。''',
    )
    profile = payload['structured_profile']
    assert profile['basic_info']['name']['value'] == '张三'
    assert profile['basic_info']['school']['value'] == '某理工大学'
    matched = {item['canonical_name'] for item in profile['skills']['matched_skills']}
    assert {'Java', 'Spring Boot', 'MySQL', 'Redis', 'Git', 'Linux'}.issubset(matched)
    assert payload['form_fill_suggestion']['manual_skills']


def test_resume_parse_extracts_experiences_and_pending_fields() -> None:
    payload = parse_resume_text(
        'resume.txt',
        '''李四
某大学 计算机科学与技术 本科 2025届
实习经历
杭州某某软件有限公司 后端开发实习生 2024.07-2024.09
参与企业后台接口开发与联调，使用 Git 与 MySQL。
校园经历
院学生会宣传部 部长 2023.09-2024.06
组织校园活动与技术分享。''',
    )
    profile = payload['structured_profile']
    internship = profile['internship_experiences'][0]
    campus = profile['campus_experiences'][0]
    assert internship['organization'] == '杭州某某软件有限公司'
    assert '开发实习生' in internship['role']
    assert campus['organization'] == '院学生会宣传部'
    assert isinstance(profile['pending_fields'], list)
    assert payload['form_fill_suggestion']['internship_experiences']


def test_resume_parse_extracts_innovation_and_certificates() -> None:
    payload = parse_resume_text(
        'resume.txt',
        '''王五
某大学 人工智能 硕士 2027届
证书
英语六级，软考中级 2025
获奖经历
全国大学生服务外包创新创业大赛二等奖
科研成果
发表 EI 会议论文 1 篇
申请发明专利 1 项
创业经历
联合创始人，负责校园服务平台产品设计。''',
    )
    innovation = payload['structured_profile']['innovation_indicators']
    assert innovation['has_awards'] is True
    assert innovation['has_publications'] is True
    assert innovation['has_patents'] is True
    assert innovation['has_entrepreneurship'] is True
    assert payload['structured_profile']['certificates']
    assert payload['form_fill_suggestion']['self_description']


def test_resume_parse_humanizes_pending_reasons() -> None:
    payload = parse_resume_text(
        'resume.txt',
        '''张三
某理工大学 软件工程 本科 2026届
项目经历
宿舍报修系统
2024.10-2025.01
使用 Redis 缓存热点数据，查询耗时从 280ms 降至 120ms。''',
    )
    reasons = [item['reason'] for item in payload['structured_profile']['pending_fields']]
    assert reasons
    assert all('heuristic' not in reason for reason in reasons)
    assert any('建议' in reason or '缺失' in reason or '未' in reason for reason in reasons)


def test_resume_parser_supports_pdf_with_fake_reader() -> None:
    original_reader = resume_parser_module.PdfReader

    class FakePage:
        def extract_text(self) -> str:
            return '张三\n某理工大学\nJava Spring Boot MySQL'

    class FakeReader:
        def __init__(self, _stream) -> None:
            self.pages = [FakePage()]

    resume_parser_module.PdfReader = FakeReader
    try:
        service = ResumeParserService()
        response = service.parse('resume.pdf', b'%PDF-1.4 fake')
        assert response.file_type == '.pdf'
        assert response.parsed_success is True
        assert '张三' in response.extracted_text
    finally:
        resume_parser_module.PdfReader = original_reader
