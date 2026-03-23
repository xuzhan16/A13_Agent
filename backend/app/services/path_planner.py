from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.job import MatchResult
from backend.app.schemas.planning import CareerPathOption, CareerPathStep
from backend.app.schemas.student import StudentProfile


class PathPlannerService:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def build_paths(
        self,
        student_profile: StudentProfile,
        match_results: list[MatchResult],
    ) -> list[CareerPathOption]:
        del student_profile
        if not match_results:
            return []

        primary = self._build_primary_path(match_results[0])
        options = [primary]

        if len(match_results) > 1:
            options.append(self._build_backup_path(match_results[1]))

        best_job = self.repository.get_job_family(match_results[0].job_family)
        if best_job and best_job.transfer_paths:
            options.append(
                CareerPathOption(
                    path_name=f'{best_job.job_family}转岗路径',
                    path_type='transfer',
                    fit_reason='结合当前相近技能栈，为后续职业弹性提供备选路线。',
                    steps=[
                        CareerPathStep(
                            role=best_job.job_family,
                            stage='当前适配岗位',
                            description='先进入相对更可获得的目标岗位，积累首份职业证据。',
                            unlock_conditions=['完成岗位核心能力补齐', '完成简历与项目集打磨'],
                        ),
                        CareerPathStep(
                            role=best_job.transfer_paths[0],
                            stage='近邻转岗',
                            description='利用相邻技能迁移，向更适配或更高成长性岗位移动。',
                            unlock_conditions=['补足相邻岗位缺口技能', '积累跨岗位项目成果'],
                        ),
                    ],
                )
            )

        return options

    def _build_primary_path(self, best_match: MatchResult) -> CareerPathOption:
        return CareerPathOption(
            path_name=f'{best_match.job_family}主路径',
            path_type='primary',
            fit_reason=f'当前综合匹配度最高，为首选职业切入方向，当前得分 {best_match.overall_score}。',
            steps=[
                CareerPathStep(
                    role=best_match.job_family,
                    stage='0-1年',
                    description='以校招/实习为切入点，补足必备技能并完成首份可量化成果。',
                    unlock_conditions=['完成目标岗位技能补齐', '完成至少1个高质量项目/实习证明'],
                ),
                CareerPathStep(
                    role='高级岗位',
                    stage='1-3年',
                    description='在稳定交付的基础上形成专项优势，争取高级岗位或核心模块负责机会。',
                    unlock_conditions=['形成专项能力标签', '获得更强项目复杂度证明'],
                ),
                CareerPathStep(
                    role='负责人/专家',
                    stage='3-5年',
                    description='向技术负责人、产品负责人或项目负责人方向发展。',
                    unlock_conditions=['具备跨团队协同能力', '形成业务与技术复合价值'],
                ),
            ],
        )

    def _build_backup_path(self, second_match: MatchResult) -> CareerPathOption:
        return CareerPathOption(
            path_name=f'{second_match.job_family}备选路径',
            path_type='backup',
            fit_reason=f'匹配度位居前列，适合作为校招或转岗的第二选择，当前得分 {second_match.overall_score}。',
            steps=[
                CareerPathStep(
                    role=second_match.job_family,
                    stage='备选切入',
                    description='作为与主路径技能邻近的岗位，能够提升求职成功率和职业弹性。',
                    unlock_conditions=['完成目标岗位关键技能补齐', '针对岗位重写简历与项目表达'],
                ),
            ],
        )
