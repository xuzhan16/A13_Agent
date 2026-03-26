from __future__ import annotations

from statistics import median

from backend.app.core.trend_catalog import (
    GENERIC_INDUSTRY_SHIFTS,
    ROLE_TREND_CONFIG,
    SKILL_TREND_CONFIG,
    TREND_SNAPSHOT_VERSION,
    TREND_UPDATED_AT,
)
from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.job import JobRequirementProfile, MatchResult
from backend.app.schemas.planning import IndustryShiftInsight, IndustryTrendAnalysis, JobHeatInsight, SkillTrendInsight, TrendMetric
from backend.app.schemas.student import StudentProfile


class IndustryTrendService:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def analyze(self, student_profile: StudentProfile, match_results: list[MatchResult]) -> IndustryTrendAnalysis:
        top_matches = match_results[:3]
        role_heat = [self._build_role_heat(item.job_family) for item in top_matches]
        missing_skill_trends = self._build_skill_trends(match_results)
        top_job = top_matches[0].job_family if top_matches else ''
        industry_shifts = self._build_industry_shifts(top_job)
        personalized_advice = self._build_personalized_advice(student_profile, top_matches, missing_skill_trends, industry_shifts)
        return IndustryTrendAnalysis(
            snapshot_version=TREND_SNAPSHOT_VERSION,
            updated_at=TREND_UPDATED_AT,
            role_heat=role_heat,
            missing_skill_trends=missing_skill_trends,
            industry_shifts=industry_shifts,
            personalized_advice=personalized_advice,
        )

    def _build_role_heat(self, job_family: str) -> JobHeatInsight:
        profile = self.repository.get_job_family(job_family)
        config = ROLE_TREND_CONFIG.get(job_family, {})
        demand_index = self._demand_index(profile, config)
        salary_index = self._salary_index(profile, config)
        growth_index = self._growth_index(config.get('growth_rate', 0.06))
        tightness_index = self._tightness_index(config.get('tightness', 1.05))
        heat_score = round(demand_index * 0.35 + salary_index * 0.25 + growth_index * 0.25 + tightness_index * 0.15, 1)
        metrics = [
            TrendMetric(metric_code='role.demand', metric_name='\u62db\u8058\u9700\u6c42\u91cf', value=profile.sample_count if profile else 0, display_value=f'{profile.sample_count if profile else 0} \u6761\u6837\u672c', score=demand_index, weight=0.35, formula='\u57fa\u4e8e\u5c97\u4f4d\u6837\u672c\u91cf\u76f8\u5bf9\u4e2d\u4f4d\u6570\u5f52\u4e00\u5316'),
            TrendMetric(metric_code='role.salary', metric_name='\u85aa\u8d44\u6c34\u5e73', value=self._salary_mid(profile) if profile else 0, display_value=self._salary_text(profile), score=salary_index, weight=0.25, formula='\u5c97\u4f4d\u4e2d\u4f4d\u6708\u85aa\u76f8\u5bf9\u5c97\u4f4d\u5e93\u6700\u9ad8\u503c\u5f52\u4e00\u5316'),
            TrendMetric(metric_code='role.growth', metric_name='\u589e\u957f\u8d8b\u52bf', value=config.get('growth_rate', 0.06), display_value=f'{round(config.get("growth_rate", 0.06) * 100, 1)}%', score=growth_index, weight=0.25, formula='\u79bb\u7ebf\u8d8b\u52bf\u5feb\u7167\u4e2d\u7684\u8fd1\u5468\u671f\u589e\u957f\u4fe1\u53f7'),
            TrendMetric(metric_code='role.tightness', metric_name='\u4f9b\u9700\u7d27\u5f20\u5ea6', value=config.get('tightness', 1.05), display_value=f'{config.get("tightness", 1.05):.2f}', score=tightness_index, weight=0.15, formula='\u79bb\u7ebf\u8d8b\u52bf\u5feb\u7167\u4e2d\u7684\u4f9b\u9700\u4ee3\u7406\u503c'),
        ]
        summary = config.get('summary') or f'{job_family}\u7684\u5e02\u573a\u70ed\u5ea6\u4e3a {heat_score}\uff0c\u9700\u6c42\u4e0e\u85aa\u8d44\u8868\u73b0\u6574\u4f53\u7a33\u5065\u3002'
        return JobHeatInsight(job_family=job_family, heat_score=heat_score, heat_level=self._heat_level(heat_score), summary=summary, metrics=metrics)

    def _build_skill_trends(self, match_results: list[MatchResult]) -> list[SkillTrendInsight]:
        ordered_skills: list[str] = []
        for result in match_results[:3]:
            for skill in result.missing_skills[:4]:
                if skill not in ordered_skills:
                    ordered_skills.append(skill)
        return [self._build_skill_trend(skill) for skill in ordered_skills[:6]]

    def _build_skill_trend(self, skill_name: str) -> SkillTrendInsight:
        profile_list = self.repository.list_job_families()
        config = SKILL_TREND_CONFIG.get(skill_name, {})
        coverage_ratio = self._skill_coverage_ratio(skill_name, profile_list, config)
        growth_rate = config.get('growth_rate', 0.08)
        salary_premium = config.get('salary_premium', 0.04)
        transferability = config.get('transferability', coverage_ratio)
        coverage_score = round(coverage_ratio * 100, 1)
        growth_score = self._growth_index(growth_rate)
        premium_score = min(100.0, round(45 + salary_premium * 220, 1))
        transfer_score = round(max(35.0, transferability * 100), 1)
        heat_score = round(coverage_score * 0.40 + growth_score * 0.25 + premium_score * 0.25 + transfer_score * 0.10, 1)
        metrics = [
            TrendMetric(metric_code='skill.coverage', metric_name='\u6280\u80fd\u9700\u6c42\u91cf', value=coverage_ratio, display_value=f'{round(coverage_ratio * 100, 1)}%', score=coverage_score, weight=0.40, formula='\u5c97\u4f4d\u753b\u50cf\u4e2d\u5305\u542b\u8be5\u6280\u80fd\u7684\u5c97\u4f4d\u5360\u6bd4'),
            TrendMetric(metric_code='skill.growth', metric_name='\u589e\u957f\u901f\u5ea6', value=growth_rate, display_value=f'{round(growth_rate * 100, 1)}%', score=growth_score, weight=0.25, formula='\u79bb\u7ebf\u8d8b\u52bf\u5feb\u7167\u4e2d\u7684\u6280\u80fd\u589e\u957f\u7387'),
            TrendMetric(metric_code='skill.premium', metric_name='\u85aa\u8d44\u6ea2\u4ef7', value=salary_premium, display_value=f'{round(salary_premium * 100, 1)}%', score=premium_score, weight=0.25, formula='\u5305\u542b\u8be5\u6280\u80fd\u7684\u5c97\u4f4d\u76f8\u5bf9\u57fa\u7ebf\u85aa\u8d44\u6ea2\u4ef7'),
            TrendMetric(metric_code='skill.transferability', metric_name='\u8de8\u5c97\u901a\u7528\u6027', value=transferability, display_value=f'{round(transferability * 100, 1)}%', score=transfer_score, weight=0.10, formula='\u8986\u76d6\u76f8\u90bb\u5c97\u4f4d\u7684\u6bd4\u4f8b'),
        ]
        summary = config.get('summary') or f'{skill_name}\u5728\u591a\u4e2a\u5c97\u4f4d\u4e2d\u6301\u7eed\u51fa\u73b0\uff0c\u5177\u5907\u7a33\u5b9a\u8865\u9f50\u4ef7\u503c\u3002'
        suggestion = self._skill_suggestion(skill_name, heat_score)
        return SkillTrendInsight(skill_name=skill_name, category='missing', heat_score=heat_score, heat_level=self._heat_level(heat_score), summary=summary, suggestion=suggestion, metrics=metrics)

    def _build_industry_shifts(self, job_family: str) -> list[IndustryShiftInsight]:
        config = ROLE_TREND_CONFIG.get(job_family, {})
        raw_items = config.get('industry_shifts') or GENERIC_INDUSTRY_SHIFTS
        return [IndustryShiftInsight(**item) for item in raw_items[:3]]

    def _build_personalized_advice(self, student_profile: StudentProfile, top_matches: list[MatchResult], missing_skill_trends: list[SkillTrendInsight], industry_shifts: list[IndustryShiftInsight]) -> list[str]:
        advice: list[str] = []
        if top_matches:
            top_job = top_matches[0].job_family
            focus_skills = ROLE_TREND_CONFIG.get(top_job, {}).get('personalized_focus', [])
            if focus_skills:
                focus_text = '\u3001'.join(focus_skills[:3])
                advice.append(f'\u672a\u6765 3 \u5e74\u5efa\u8bae\u56f4\u7ed5\u201c{top_job}\u201d\u4e3b\u8def\u5f84\uff0c\u4f18\u5148\u8865\u9f50\uff1a{focus_text}\u3002')
        if missing_skill_trends:
            top_skill = max(missing_skill_trends, key=lambda item: item.heat_score)
            advice.append(f'\u5f53\u524d\u6700\u503c\u5f97\u4f18\u5148\u8865\u5f3a\u7684\u7f3a\u53e3\u6280\u80fd\u662f\u201c{top_skill.skill_name}\u201d\uff0c\u56e0\u4e3a\u5b83\u7684\u5e02\u573a\u70ed\u5ea6\u8fbe\u5230 {top_skill.heat_score}\u3002')
        if industry_shifts:
            advice.append(f'\u884c\u4e1a\u53d8\u5316\u63d0\u793a\uff1a{industry_shifts[0].topic} \u6b63\u5728\u6539\u53d8\u5c97\u4f4d\u8981\u6c42\uff0c\u5efa\u8bae\u628a\u76f8\u5173\u80fd\u529b\u5199\u8fdb\u9879\u76ee\u6216\u4f5c\u54c1\u4e2d\u3002')
        if '\u5b66\u4e60\u80fd\u529b' in student_profile.soft_skills or any(item.skill_code == 'learning_agility' and item.score >= 75 for item in student_profile.soft_skill_assessments):
            advice.append('\u4f60\u7684\u5b66\u4e60\u80fd\u529b\u57fa\u7840\u8f83\u597d\uff0c\u9002\u5408\u628a\u8d8b\u52bf\u6280\u80fd\u548c\u73b0\u6709\u4e3b\u6280\u80fd\u6808\u7ec4\u5408\uff0c\u5f62\u6210\u66f4\u6709\u8fa8\u8bc6\u5ea6\u7684\u80fd\u529b\u6807\u7b7e\u3002')
        if not advice:
            advice.append('\u5efa\u8bae\u6301\u7eed\u8ddf\u8e2a\u76ee\u6807\u5c97\u4f4d\u7684\u6280\u80fd\u53d8\u5316\uff0c\u5e76\u6bcf\u6708\u590d\u76d8\u4e00\u6b21\u7b80\u5386\u4e0e\u9879\u76ee\u65b9\u5411\u3002')
        return advice[:4]

    def _demand_index(self, profile: JobRequirementProfile | None, config: dict) -> float:
        if not profile or profile.sample_count <= 0:
            return float(config.get('demand_index', 58))
        sample_counts = [item.sample_count for item in self.repository.list_job_families() if item.sample_count > 0]
        if not sample_counts:
            return float(config.get('demand_index', 58))
        baseline = max(median(sample_counts), 1)
        return round(min(100.0, 45 + profile.sample_count / baseline * 30), 1)

    def _salary_index(self, profile: JobRequirementProfile | None, config: dict) -> float:
        if not profile:
            return float(config.get('salary_index', 60))
        mids = [self._salary_mid(item) for item in self.repository.list_job_families() if self._salary_mid(item) > 0]
        salary_mid = self._salary_mid(profile)
        if not mids or salary_mid <= 0:
            return float(config.get('salary_index', 60))
        return round(min(100.0, 40 + salary_mid / max(mids) * 60), 1)

    @staticmethod
    def _growth_index(growth_rate: float) -> float:
        return round(max(45.0, min(100.0, 50 + growth_rate * 140)), 1)

    @staticmethod
    def _tightness_index(tightness: float) -> float:
        return round(max(45.0, min(100.0, tightness * 55)), 1)

    @staticmethod
    def _salary_mid(profile: JobRequirementProfile) -> float:
        min_salary = profile.salary_min_monthly or 0
        max_salary = profile.salary_max_monthly or 0
        if min_salary and max_salary:
            return round((min_salary + max_salary) / 2, 1)
        return float(max_salary or min_salary or 0)

    def _salary_text(self, profile: JobRequirementProfile | None) -> str:
        if not profile:
            return '\u7f3a\u5c11\u85aa\u8d44\u5feb\u7167'
        min_salary = profile.salary_min_monthly
        max_salary = profile.salary_max_monthly
        if min_salary and max_salary:
            return f'{round(min_salary, 1)}K - {round(max_salary, 1)}K / \u6708'
        if min_salary or max_salary:
            return f'{round(float(min_salary or max_salary), 1)}K / \u6708'
        return '\u7f3a\u5c11\u85aa\u8d44\u5feb\u7167'

    @staticmethod
    def _heat_level(score: float) -> str:
        if score >= 80:
            return '\u70ed'
        if score >= 65:
            return '\u504f\u70ed'
        if score >= 50:
            return '\u5e73\u7a33'
        return '\u89c2\u5bdf'

    def _skill_coverage_ratio(self, skill_name: str, profiles: list[JobRequirementProfile], config: dict) -> float:
        matched = 0
        for profile in profiles:
            skills = set(profile.required_skills + profile.bonus_skills)
            if skill_name in skills:
                matched += 1
        if profiles and matched:
            return round(matched / len(profiles), 4)
        return float(config.get('demand_ratio', 0.28))

    @staticmethod
    def _skill_suggestion(skill_name: str, heat_score: float) -> str:
        if heat_score >= 75:
            return f'{skill_name} \u5904\u4e8e\u9ad8\u70ed\u5ea6\u533a\u95f4\uff0c\u5efa\u8bae\u4f18\u5148\u5b89\u6392\u5230\u672a\u6765 1-2 \u4e2a\u9879\u76ee\u4e2d\u3002'
        if heat_score >= 60:
            return f'{skill_name} \u5177\u5907\u7a33\u5b9a\u8865\u9f50\u4ef7\u503c\uff0c\u5efa\u8bae\u5728\u672a\u6765\u4e00\u4e2a\u5b63\u5ea6\u5185\u8865\u9f50\u3002'
        return f'{skill_name} \u70ed\u5ea6\u4e2d\u7b49\uff0c\u53ef\u7ed3\u5408\u76ee\u6807\u5c97\u4f4d\u573a\u666f\u6309\u9700\u8865\u5145\u3002'
