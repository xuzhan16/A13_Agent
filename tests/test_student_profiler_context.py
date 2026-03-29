import json

from backend.app.infra.llm.base import LLMClient
from backend.app.schemas.job import JobRequirementProfile
from backend.app.schemas.student import CareerPreference, StudentBasicInfo, StudentIntakeRequest
from backend.app.services.soft_skill_assessor import SoftSkillAssessmentService
from backend.app.services.student_profiler import StudentProfilerService


class _RepoStub:
    def get_skill_lexicon(self):
        return ['Java', 'Spring Boot', 'MySQL', 'Redis']

    def get_soft_skill_lexicon(self):
        return ['沟通能力', '学习能力', '执行力']

    def list_job_families(self):
        return [
            JobRequirementProfile(job_family='Java开发工程师', description='backend role'),
            JobRequirementProfile(job_family='软件测试工程师', description='qa role'),
        ]


class _LLMStub(LLMClient):
    def __init__(self):
        self.last_prompt = ''

    @property
    def enabled(self) -> bool:
        return True

    def generate(self, prompt: str, system_prompt: str = '') -> str:
        del system_prompt
        self.last_prompt = prompt
        return json.dumps(
            {
                'hard_skills': ['Java', 'LangChain'],
                'soft_skills': ['沟通能力', '情绪稳定'],
                'certificates': ['CET-4'],
                'inferred_strengths': ['结构化表达'],
                'inferred_gaps': ['缺少实习'],
                'evidences': ['参与后端项目并完成接口开发'],
                'summary': 'LLM summary',
            },
            ensure_ascii=False,
        )


def test_student_profiler_uses_neo4j_context_and_validates_llm_skills():
    llm = _LLMStub()
    service = StudentProfilerService(_RepoStub(), SoftSkillAssessmentService(), llm_client=llm)
    intake = StudentIntakeRequest(
        basic_info=StudentBasicInfo(name='Alice', school='Demo University', major='Software Engineering', degree='Bachelor', graduation_year=2026),
        preference=CareerPreference(target_roles=['Java开发工程师'], target_cities=['深圳'], desired_industries=['互联网']),
        resume_text='Worked on Java backend APIs with Spring Boot and MySQL.',
        self_description='Fast learner and strong communicator.',
        manual_skills=['Java'],
        project_experiences=['Built a backend service with Spring Boot and MySQL.'],
        internship_experiences=[],
        campus_experiences=['Organized project demo day.'],
        certificates=['CET-4'],
        follow_up_answers=[],
    )

    profile = service.build_profile(intake)

    assert 'LangChain' not in profile.hard_skills
    assert 'Java' in profile.hard_skills
    assert '沟通能力' in profile.soft_skills
    assert '情绪稳定' not in profile.soft_skills
    assert profile.profile_source == 'llm_augmented'
    assert 'Available hard skills from knowledge base' in llm.last_prompt
    assert 'Java开发工程师' in llm.last_prompt
