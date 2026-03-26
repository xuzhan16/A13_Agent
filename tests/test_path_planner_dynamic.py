from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.graph import JobGraph
from backend.app.schemas.job import JobRequirementProfile, MatchResult
from backend.app.schemas.planning import TransferPathEdge, TransferPathResult
from backend.app.schemas.student import CareerPreference, StudentBasicInfo, StudentProfile
from backend.app.services.path_planner import PathPlannerService


class _FakeRepository(KnowledgeRepository):
    def list_job_families(self):
        return []

    def get_job_family(self, job_family: str):
        if job_family == 'Java开发工程师':
            return JobRequirementProfile(
                job_family='Java开发工程师',
                description='后端开发',
                vertical_growth_path=['Java开发工程师', '高级开发工程师', '技术负责人', '架构师'],
                transfer_paths=['软件测试工程师'],
            )
        if job_family == '软件测试工程师':
            return JobRequirementProfile(
                job_family='软件测试工程师',
                description='测试岗位',
                vertical_growth_path=['软件测试工程师', '高级测试工程师', '测试负责人'],
            )
        return None

    def get_skill_lexicon(self):
        return []

    def get_soft_skill_lexicon(self):
        return []

    def get_job_graph(self):
        return JobGraph()

    def get_personalized_paths(self, from_job, student_skills, target_job=None, max_steps=5, limit=10):
        del student_skills, max_steps, limit
        if from_job == 'Java开发工程师' and target_job == '架构师':
            return [
                TransferPathResult(
                    jobs=['Java开发工程师', '高级开发工程师', '技术负责人', '架构师'],
                    steps=3,
                    cumulative_success_rate=0.49,
                    estimated_time_cost='3-5年',
                    difficulty='high',
                    ready_ratio=0.5,
                    is_feasible=False,
                    missing_skills=['系统设计', '分布式架构'],
                    edge_chain=[
                        TransferPathEdge(
                            source_job='Java开发工程师',
                            target_job='高级开发工程师',
                            relation_type='VERTICAL_TO',
                            success_rate=0.86,
                            time_cost='1-2年',
                            required_skills=['微服务'],
                            missing_skills=[],
                            evidence=['catalog'],
                        ),
                        TransferPathEdge(
                            source_job='高级开发工程师',
                            target_job='技术负责人',
                            relation_type='VERTICAL_TO',
                            success_rate=0.79,
                            time_cost='1-2年',
                            required_skills=['系统设计'],
                            missing_skills=['系统设计'],
                            evidence=['行业报告'],
                        ),
                        TransferPathEdge(
                            source_job='技术负责人',
                            target_job='架构师',
                            relation_type='VERTICAL_TO',
                            success_rate=0.72,
                            time_cost='1-2年',
                            required_skills=['分布式架构'],
                            missing_skills=['分布式架构'],
                            evidence=['真实案例'],
                        ),
                    ],
                )
            ]
        if from_job == 'Java开发工程师' and target_job == '软件测试工程师':
            return [
                TransferPathResult(
                    jobs=['Java开发工程师', '软件测试工程师'],
                    steps=1,
                    cumulative_success_rate=0.68,
                    estimated_time_cost='6-12个月',
                    difficulty='medium',
                    ready_ratio=0.75,
                    is_feasible=False,
                    missing_skills=['测试用例设计'],
                    edge_chain=[
                        TransferPathEdge(
                            source_job='Java开发工程师',
                            target_job='软件测试工程师',
                            relation_type='TRANSFER_TO',
                            success_rate=0.68,
                            time_cost='6-12个月',
                            required_skills=['测试用例设计'],
                            missing_skills=['测试用例设计'],
                            evidence=['技能邻近性'],
                        )
                    ],
                )
            ]
        return []


def test_path_planner_uses_graph_path_results():
    repo = _FakeRepository()
    service = PathPlannerService(repo)
    student = StudentProfile(
        basic_info=StudentBasicInfo(name='C', major='软件工程'),
        preference=CareerPreference(target_roles=['Java开发工程师']),
        hard_skills=['Java', 'Spring Boot', 'MySQL', '接口设计'],
        soft_skills=['学习能力'],
        certificates=['英语四级'],
    )
    matches = [
        MatchResult(job_family='Java开发工程师', overall_score=88, summary='best'),
        MatchResult(job_family='软件测试工程师', overall_score=76, summary='backup'),
    ]

    options = service.build_paths(student, matches)

    assert options[0].path_jobs[-1] == '架构师'
    assert options[0].estimated_time_cost == '3-5年'
    assert '系统设计' in options[0].missing_skills
    assert options[2].path_type == 'transfer'
    assert options[2].target_role == '软件测试工程师'
