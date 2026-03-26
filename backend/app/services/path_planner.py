from typing import Optional

from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.job import MatchResult
from backend.app.schemas.planning import CareerPathOption, CareerPathStep, TransferPathResult
from backend.app.schemas.student import StudentProfile


class PathPlannerService:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def build_paths(
        self,
        student_profile: StudentProfile,
        match_results: list[MatchResult],
    ) -> list[CareerPathOption]:
        if not match_results:
            return []

        student_skills = self._build_student_skill_pool(student_profile)
        options: list[CareerPathOption] = []

        primary = self._build_primary_path(student_profile, match_results[0], student_skills)
        options.append(primary)

        if len(match_results) > 1:
            options.append(self._build_backup_path(match_results[1], student_skills))

        transfer_option = self._build_transfer_path(match_results[0].job_family, student_skills)
        if transfer_option is not None:
            options.append(transfer_option)

        return options

    def _build_primary_path(
        self,
        student_profile: StudentProfile,
        best_match: MatchResult,
        student_skills: list[str],
    ) -> CareerPathOption:
        del student_profile
        profile = self.repository.get_job_family(best_match.job_family)
        dynamic_path = self._resolve_growth_path(best_match.job_family, profile.vertical_growth_path if profile else [], student_skills)
        if dynamic_path is not None:
            return self._option_from_result(
                result=dynamic_path,
                path_name=f'{best_match.job_family}主路径',
                path_type='primary',
                base_reason=(
                    f'当前综合匹配度最高，为首选职业切入方向，当前得分 {best_match.overall_score}。'
                    f'结合岗位成长图谱，已推演到 {dynamic_path.jobs[-1]} 的中长期成长路径。'
                ),
            )
        return self._build_primary_path_fallback(best_match)

    def _build_backup_path(self, second_match: MatchResult, student_skills: list[str]) -> CareerPathOption:
        profile = self.repository.get_job_family(second_match.job_family)
        dynamic_path = self._resolve_growth_path(second_match.job_family, profile.vertical_growth_path if profile else [], student_skills)
        if dynamic_path is not None:
            return self._option_from_result(
                result=dynamic_path,
                path_name=f'{second_match.job_family}备选路径',
                path_type='backup',
                base_reason=(
                    f'匹配度位居前列，适合作为校招或转岗的第二选择，当前得分 {second_match.overall_score}。'
                    '该路径能在保持技能邻近性的同时，提供更稳的上升路线。'
                ),
            )
        return self._build_backup_path_fallback(second_match)

    def _build_transfer_path(self, from_job: str, student_skills: list[str]) -> Optional[CareerPathOption]:
        profile = self.repository.get_job_family(from_job)
        if profile is None or not profile.transfer_paths:
            return None

        candidates: list[TransferPathResult] = []
        for target_job in profile.transfer_paths:
            paths = self.repository.get_personalized_paths(
                from_job=from_job,
                student_skills=student_skills,
                target_job=target_job,
                max_steps=3,
                limit=3,
            )
            if paths:
                candidates.append(paths[0])

        if not candidates:
            return None

        best = sorted(
            candidates,
            key=lambda item: (not item.is_feasible, -item.ready_ratio, -item.cumulative_success_rate, item.steps),
        )[0]
        return self._option_from_result(
            result=best,
            path_name=f'{from_job}转岗路径',
            path_type='transfer',
            base_reason='结合当前相近技能栈，为后续职业弹性提供备选路线。',
        )

    def _resolve_growth_path(
        self,
        from_job: str,
        vertical_growth_path: list[str],
        student_skills: list[str],
    ) -> Optional[TransferPathResult]:
        if len(vertical_growth_path) < 2:
            return None
        target_job = vertical_growth_path[-1]
        max_steps = max(3, len(vertical_growth_path) - 1)
        paths = self.repository.get_personalized_paths(
            from_job=from_job,
            student_skills=student_skills,
            target_job=target_job,
            max_steps=max_steps,
            limit=3,
        )
        return paths[0] if paths else None

    def _option_from_result(
        self,
        result: TransferPathResult,
        path_name: str,
        path_type: str,
        base_reason: str,
    ) -> CareerPathOption:
        readiness_score = round(result.ready_ratio * 100, 1)
        cumulative_success_pct = round(result.cumulative_success_rate * 100, 1)
        evidence_sources = self._unique(source for edge in result.edge_chain for source in edge.evidence)

        steps: list[CareerPathStep] = [
            CareerPathStep(
                role=result.jobs[0],
                stage='当前起点',
                description='先进入起点岗位并沉淀可验证成果，为后续进阶建立真实职业证据。',
                unlock_conditions=['完成岗位核心能力补齐', '形成可量化项目或实习成果'],
            )
        ]
        for index, edge in enumerate(result.edge_chain, start=1):
            relation_label = '纵向进阶' if edge.relation_type == 'VERTICAL_TO' else '转岗跃迁'
            unlock_conditions: list[str] = []
            if edge.required_skills:
                unlock_conditions.append(f'关键能力：{"、".join(edge.required_skills)}')
            if edge.missing_skills:
                unlock_conditions.append(f'优先补齐：{"、".join(edge.missing_skills)}')
            if edge.evidence:
                unlock_conditions.append(f'证据来源：{"；".join(edge.evidence[:2])}')
            steps.append(
                CareerPathStep(
                    role=edge.target_job,
                    stage=f'第{index}步',
                    description=(
                        f'{relation_label}至 {edge.target_job}，预计耗时 {edge.time_cost or "1-2年"}，'
                        f'该步成功率约 {round(edge.success_rate * 100, 1)}%。'
                    ),
                    unlock_conditions=unlock_conditions,
                    step_type=edge.relation_type.lower(),
                    success_rate=edge.success_rate,
                    time_cost=edge.time_cost,
                    required_skills=edge.required_skills,
                    missing_skills=edge.missing_skills,
                    evidence=edge.evidence,
                )
            )

        fit_reason = (
            f'{base_reason} 预计总耗时 {result.estimated_time_cost or "1-2年"}，'
            f'累计成功率约 {cumulative_success_pct}%，当前准备度 {readiness_score}%。'
        )
        if result.missing_skills:
            fit_reason += f' 当前主要缺口为：{"、".join(result.missing_skills[:4])}。'

        return CareerPathOption(
            path_name=path_name,
            path_type=path_type,
            fit_reason=fit_reason,
            steps=steps,
            target_role=result.jobs[-1] if result.jobs else '',
            path_jobs=result.jobs,
            readiness_score=readiness_score,
            estimated_success_rate=result.cumulative_success_rate,
            estimated_time_cost=result.estimated_time_cost,
            missing_skills=result.missing_skills,
            evidence_sources=evidence_sources,
        )

    def _build_primary_path_fallback(self, best_match: MatchResult) -> CareerPathOption:
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

    def _build_backup_path_fallback(self, second_match: MatchResult) -> CareerPathOption:
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

    @staticmethod
    def _build_student_skill_pool(student_profile: StudentProfile) -> list[str]:
        return PathPlannerService._unique(
            [
                *student_profile.hard_skills,
                *student_profile.soft_skills,
                *student_profile.certificates,
            ]
        )

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            text = str(value).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
        return result
