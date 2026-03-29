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
        dynamic_path = self._resolve_growth_path(
            best_match.job_family,
            profile.vertical_growth_path if profile else [],
            student_skills,
        )
        related_jobs = self._related_job_names(best_match.job_family, limit=3)
        target_role = dynamic_path.jobs[-1] if dynamic_path and dynamic_path.jobs else best_match.job_family
        common_entry_roles = self._common_entry_roles(target_role, best_match.job_family)
        if dynamic_path is not None:
            return self._option_from_result(
                result=dynamic_path,
                path_name=f'{best_match.job_family}主路径',
                path_type='primary',
                base_reason=(
                    f'该岗位是当前最高匹配岗位，综合得分为 {best_match.overall_score}，'
                    f'知识图谱推演显示可以沿纵向成长路线逐步走向 {dynamic_path.jobs[-1]}。'
                ),
                related_jobs=related_jobs,
                common_entry_roles=common_entry_roles,
            )
        fallback = self._build_primary_path_fallback(best_match)
        fallback.related_jobs = related_jobs
        fallback.common_entry_roles = common_entry_roles
        return fallback

    def _build_backup_path(self, second_match: MatchResult, student_skills: list[str]) -> CareerPathOption:
        profile = self.repository.get_job_family(second_match.job_family)
        dynamic_path = self._resolve_growth_path(
            second_match.job_family,
            profile.vertical_growth_path if profile else [],
            student_skills,
        )
        related_jobs = self._related_job_names(second_match.job_family, limit=3)
        common_entry_roles = self._common_entry_roles(second_match.job_family, second_match.job_family)
        if dynamic_path is not None:
            return self._option_from_result(
                result=dynamic_path,
                path_name=f'{second_match.job_family}备选路径',
                path_type='backup',
                base_reason=(
                    f'该岗位是当前第二推荐岗位，综合得分为 {second_match.overall_score}，'
                    '适合作为主路径之外的稳健备选。'
                ),
                related_jobs=related_jobs,
                common_entry_roles=common_entry_roles,
            )
        fallback = self._build_backup_path_fallback(second_match)
        fallback.related_jobs = related_jobs
        fallback.common_entry_roles = common_entry_roles
        return fallback

    def _build_transfer_path(self, from_job: str, student_skills: list[str]) -> Optional[CareerPathOption]:
        profile = self.repository.get_job_family(from_job)
        recommendation_targets = self._related_job_names(from_job, limit=5)
        explicit_targets = list(profile.transfer_paths) if profile is not None else []
        candidate_targets = [target for target in self._unique([*explicit_targets, *recommendation_targets]) if target != from_job]
        if not candidate_targets:
            return None

        candidates: list[TransferPathResult] = []
        for target_job in candidate_targets:
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
        common_entry_roles = self._common_entry_roles(best.jobs[-1] if best.jobs else from_job, from_job)
        return self._option_from_result(
            result=best,
            path_name=f'{from_job}转岗路径',
            path_type='transfer',
            base_reason='知识图谱显示该岗位存在可行的横向迁移机会，适合结合当前技能做转岗准备。',
            related_jobs=recommendation_targets,
            common_entry_roles=common_entry_roles,
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
        related_jobs: Optional[list[str]] = None,
        common_entry_roles: Optional[list[str]] = None,
    ) -> CareerPathOption:
        readiness_score = round(result.ready_ratio * 100, 1)
        cumulative_success_pct = round(result.cumulative_success_rate * 100, 1)
        evidence_sources = self._unique(source for edge in result.edge_chain for source in edge.evidence)
        related_jobs = self._unique(related_jobs or [])
        common_entry_roles = self._unique(common_entry_roles or [])

        steps: list[CareerPathStep] = [
            CareerPathStep(
                role=result.jobs[0],
                stage='当前阶段',
                description='先在当前岗位夸实核心技能与项目证据，为下一步跃迁打基础。',
                unlock_conditions=['稳定输出项目成果', '补齐关键岗位能力'],
            )
        ]
        for index, edge in enumerate(result.edge_chain, start=1):
            relation_label = '纵向晋升' if edge.relation_type == 'VERTICAL_TO' else '横向转岗'
            unlock_conditions: list[str] = []
            if edge.required_skills:
                unlock_conditions.append(f'需具备：{"、".join(edge.required_skills)}')
            if edge.missing_skills:
                unlock_conditions.append(f'待补齐：{"、".join(edge.missing_skills)}')
            if edge.evidence:
                unlock_conditions.append(f'证据：{"、".join(edge.evidence[:2])}')
            steps.append(
                CareerPathStep(
                    role=edge.target_job,
                    stage=f'第{index}步',
                    description=(
                        f'{relation_label}至 {edge.target_job}，预计耗时 {edge.time_cost or "1-2年"}，'
                        f'单步成功率 {round(edge.success_rate * 100, 1)}%。'
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
            f'路径累计成功率 {cumulative_success_pct}%，当前准备度 {readiness_score}%。'
        )
        if result.missing_skills:
            fit_reason += f' 主要缺口：{"、".join(result.missing_skills[:4])}。'
        if related_jobs:
            fit_reason += f' 图谱相邻岗位：{"、".join(related_jobs[:3])}。'
        if common_entry_roles:
            fit_reason += f' 常见入口岗位：{"、".join(common_entry_roles[:3])}。'

        evidence_bundle = self._unique([
            *evidence_sources,
            'Neo4j related job recommendation' if related_jobs else '',
            'Neo4j entry-point query' if common_entry_roles else '',
        ])

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
            evidence_sources=evidence_bundle,
            related_jobs=related_jobs,
            common_entry_roles=common_entry_roles,
        )

    def _build_primary_path_fallback(self, best_match: MatchResult) -> CareerPathOption:
        return CareerPathOption(
            path_name=f'{best_match.job_family}主路径',
            path_type='primary',
            fit_reason=f'该岗位是当前最高匹配岗位，综合得分为 {best_match.overall_score}。',
            steps=[
                CareerPathStep(
                    role=best_match.job_family,
                    stage='0-1年',
                    description='先以实习或初级岗位切入，完成从校园到岗位的第一步。',
                    unlock_conditions=['补齐岗位核心技能', '完成 1 个可展示项目或实习'],
                ),
                CareerPathStep(
                    role='进阶岗位',
                    stage='1-3年',
                    description='围绕核心业务和工程能力持续进阶。',
                    unlock_conditions=['扩大项目复杂度', '积累可量化成果'],
                ),
                CareerPathStep(
                    role='高级岗位/管理岗位',
                    stage='3-5年',
                    description='积累复杂项目和系统化经验，向高级岗位或管理岗位发展。',
                    unlock_conditions=['提升系统设计能力', '具备带项目或带人经验'],
                ),
            ],
        )

    def _build_backup_path_fallback(self, second_match: MatchResult) -> CareerPathOption:
        return CareerPathOption(
            path_name=f'{second_match.job_family}备选路径',
            path_type='backup',
            fit_reason=f'该岗位是当前第二推荐岗位，综合得分为 {second_match.overall_score}。',
            steps=[
                CareerPathStep(
                    role=second_match.job_family,
                    stage='探索阶段',
                    description='可作为备选路径持续跟踪，用于拓展求职选择面。',
                    unlock_conditions=['维持相关岗位关注度', '定期更新备选路径的项目证据'],
                ),
            ],
        )

    def _related_job_names(self, job_name: str, limit: int = 3) -> list[str]:
        try:
            recommendations = self.repository.get_job_recommendations(job_name, limit=limit)
        except Exception:
            return []
        return [item.job_family for item in recommendations if item.job_family != job_name]

    def _common_entry_roles(self, target_job: str, current_job: str, limit: int = 3) -> list[str]:
        try:
            entry_points = self.repository.get_job_entry_points(target_job, max_steps=4)
        except Exception:
            return []
        roles = []
        for path in entry_points:
            if not path.jobs:
                continue
            start = path.jobs[0]
            if start == current_job:
                continue
            roles.append(start)
        return self._unique(roles)[:limit]

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
