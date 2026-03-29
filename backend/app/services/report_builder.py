import json
from typing import Optional

from backend.app.infra.json_utils import try_parse_json
from backend.app.infra.llm.base import LLMClient
from backend.app.prompts.templates import REPORT_ENHANCEMENT_SYSTEM_PROMPT
from backend.app.schemas.job import MatchResult
from backend.app.schemas.planning import ActionPlanItem, CareerPathOption, CareerReport, IndustryTrendAnalysis
from backend.app.schemas.student import StudentProfile
from backend.app.services.industry_trend import IndustryTrendService


class ReportBuilderService:
    def __init__(
        self,
        trend_service: IndustryTrendService,
        llm_client: Optional[LLMClient] = None,
    ) -> None:
        self.trend_service = trend_service
        self.llm_client = llm_client

    def build(
        self,
        student_profile: StudentProfile,
        match_results: list[MatchResult],
        path_options: list[CareerPathOption],
    ) -> CareerReport:
        top_matches = match_results[:3]
        industry_trend = self.trend_service.analyze(student_profile, match_results)
        highlights = [
            f'画像完整度：{student_profile.completeness_score}',
            f'竞争力评分：{student_profile.competitiveness_score}',
        ]
        highlights.extend(f'{item.job_family} 匹配度 {item.overall_score}' for item in top_matches)
        if student_profile.soft_skill_assessments:
            strongest = max(student_profile.soft_skill_assessments, key=lambda item: item.score)
            highlights.append(f'软素质优势：{strongest.skill_name} {strongest.score}')
        if industry_trend.role_heat:
            hottest = industry_trend.role_heat[0]
            highlights.append(f'市场热度：{hottest.job_family} {hottest.heat_score} ({hottest.heat_level})')
        if path_options and path_options[0].target_role:
            highlights.append(f'成长终点：{path_options[0].target_role}')

        action_plan = self._build_action_plan(top_matches, industry_trend, path_options)
        overview = '基于学生画像、岗位要求画像、软素质显式评分、知识图谱路径推演与行业趋势快照生成的证据驱动职业规划建议。'
        executive_summary = self._build_executive_summary(student_profile, top_matches, industry_trend, path_options)
        markdown = self._build_markdown(student_profile, top_matches, path_options, action_plan, executive_summary, industry_trend)
        generation_mode = 'template'

        enhanced = self._enhance_with_llm(
            student_profile=student_profile,
            top_matches=top_matches,
            path_options=path_options,
            action_plan=action_plan,
            markdown=markdown,
            executive_summary=executive_summary,
            industry_trend=industry_trend,
        )
        if enhanced:
            executive_summary = enhanced.get('executive_summary', executive_summary) or executive_summary
            markdown = enhanced.get('report_markdown', markdown) or markdown
            overview = enhanced.get('overview', overview) or overview
            generation_mode = 'llm_augmented'

        return CareerReport(
            title='大学生职业生涯发展报告',
            overview=overview,
            executive_summary=executive_summary,
            highlight_points=highlights,
            recommended_paths=path_options,
            action_plan=action_plan,
            report_markdown=markdown,
            generation_mode=generation_mode,
            industry_trend=industry_trend,
        )

    @staticmethod
    def _build_action_plan(
        top_matches: list[MatchResult],
        industry_trend: IndustryTrendAnalysis,
        path_options: list[CareerPathOption],
    ) -> list[ActionPlanItem]:
        primary = top_matches[0] if top_matches else None
        path_gap_skills = path_options[0].missing_skills[:3] if path_options else []
        gaps = path_gap_skills or (primary.missing_skills[:3] if primary else [])
        trend_skills = [item.skill_name for item in industry_trend.missing_skill_trends[:2]]

        return [
            ActionPlanItem(
                phase='30天',
                objective='完成职业定位与求职材料重构',
                actions=[
                    '明确主路径和备选路径各1条',
                    '围绕目标岗位重写简历与项目表达',
                    '梳理3段可量化的能力证据',
                ],
                metrics=['完成1版目标岗位简历', '完成1版项目集说明', '完成岗位差距清单'],
            ),
            ActionPlanItem(
                phase='90天',
                objective='补齐岗位核心差距并形成作品',
                actions=[
                    *[f'补齐技能：{item}' for item in gaps],
                    *[f'优先跟进趋势技能：{item}' for item in trend_skills if item not in gaps],
                    '完成1个贴近目标岗位的综合项目',
                    '完成至少10次模拟面试或岗位问答训练',
                ],
                metrics=['新增1个可展示项目', '核心差距至少关闭2项', '形成标准化面试题库'],
            ),
            ActionPlanItem(
                phase='180天',
                objective='拿到高质量实习或校招机会',
                actions=[
                    '建立岗位投递与复盘看板',
                    '针对主路径和备选路径双线投递',
                    '持续复盘面试反馈并更新行动计划',
                ],
                metrics=['形成周复盘机制', '获得目标岗位面试机会', '输出动态迭代版职业规划'],
            ),
        ]

    @staticmethod
    def _build_executive_summary(
        student_profile: StudentProfile,
        top_matches: list[MatchResult],
        industry_trend: IndustryTrendAnalysis,
        path_options: list[CareerPathOption],
    ) -> str:
        if not top_matches:
            return '当前信息不足，建议先补齐关键经历与技能后再生成详细规划。'
        top = top_matches[0]
        strongest_soft = max(student_profile.soft_skill_assessments, key=lambda item: item.score).skill_name if student_profile.soft_skill_assessments else '职业素养'
        gaps = '、'.join(top.missing_skills[:3]) or '暂无明显关键技能缺口'
        trend_focus = industry_trend.missing_skill_trends[0].skill_name if industry_trend.missing_skill_trends else '趋势技能'
        path_hint = ''
        if path_options:
            primary = path_options[0]
            path_hint = f'知识图谱推演显示，你从“{primary.path_jobs[0] if primary.path_jobs else top.job_family}”走向“{primary.target_role or top.job_family}”的当前准备度约为 {primary.readiness_score}%。'
        return (
            f'当前最推荐优先冲刺“{top.job_family}”，综合匹配度为 {top.overall_score}。'
            f'你当前最突出的软素质是：{strongest_soft}；'
            f'短期内最值得补强的是：{gaps}，其中市场热度最高的缺口技能是：{trend_focus}。'
            f'{path_hint}'
        )

    def _build_markdown(
        self,
        student_profile: StudentProfile,
        top_matches: list[MatchResult],
        path_options: list[CareerPathOption],
        action_plan: list[ActionPlanItem],
        executive_summary: str,
        industry_trend: IndustryTrendAnalysis,
    ) -> str:
        hard_skills_text = '、'.join(student_profile.hard_skills) or '待补充'
        soft_skills_text = '、'.join(student_profile.soft_skills) or '待补充'
        strengths_text = '、'.join(student_profile.inferred_strengths) or '待补充'
        gaps_text = '、'.join(student_profile.inferred_gaps) or '待补充'
        major_text = student_profile.basic_info.major or '待补充'
        lines = [
            '# 大学生职业生涯发展报告',
            '',
            '## 一、执行摘要',
            executive_summary,
            '',
            '## 二、学生画像概览',
            f'- 专业：{major_text}',
            f'- 完整度：{student_profile.completeness_score}',
            f'- 竞争力：{student_profile.competitiveness_score}',
            f'- 已识别硬技能：{hard_skills_text}',
            f'- 已识别软素质：{soft_skills_text}',
            f'- 主要优势：{strengths_text}',
            f'- 主要短板：{gaps_text}',
            '',
            '## 三、软素质显式画像',
        ]

        for assessment in student_profile.soft_skill_assessments:
            suggestion_text = '；'.join(assessment.suggestions) if assessment.suggestions else '继续保持'
            lines.extend([
                f'### {assessment.skill_name}',
                f'- 分数：{assessment.score}',
                f'- 等级：{assessment.level}',
                f'- 结论：{assessment.summary}',
                f'- 建议：{suggestion_text}',
                '',
            ])

        lines.append('## 四、推荐岗位')
        for result in top_matches:
            matched_skills_text = '、'.join(result.matched_skills) or '待补充'
            missing_skills_text = '、'.join(result.missing_skills) or '无明显短板'
            lines.extend([
                f'### {result.job_family}',
                f'- 综合匹配度：{result.overall_score}',
                f'- 优势技能：{matched_skills_text}',
                f'- 待补技能：{missing_skills_text}',
                f'- 结论：{result.summary}',
                '',
            ])

        lines.append('## 五、职业路径建议')
        for option in path_options:
            lines.append(f'### {option.path_name}')
            lines.append(f'- 类型：{option.path_type}')
            lines.append(f'- 原因：{option.fit_reason}')
            if option.path_jobs:
                lines.append(f'- 路径链路：{" -> ".join(option.path_jobs)}')
            if option.target_role:
                lines.append(f'- 目标终点：{option.target_role}')
            if option.estimated_success_rate:
                lines.append(f'- 累计成功率：{round(option.estimated_success_rate * 100, 1)}%')
            if option.estimated_time_cost:
                lines.append(f'- 预计时间成本：{option.estimated_time_cost}')
            if option.readiness_score:
                lines.append(f'- 当前准备度：{option.readiness_score}%')
            if option.missing_skills:
                lines.append(f'- 路径总缺口：{"、".join(option.missing_skills)}')
            if option.related_jobs:
                lines.append(f'- \u56fe\u8c31\u76f8\u90bb\u5c97\u4f4d\uff1a{chr(12289).join(option.related_jobs)}')
            if option.common_entry_roles:
                lines.append(f'- \u5e38\u89c1\u5165\u53e3\u5c97\u4f4d\uff1a{chr(12289).join(option.common_entry_roles)}')
            if option.evidence_sources:
                lines.append(f'- 证据来源：{"；".join(option.evidence_sources)}')
            for step in option.steps:
                lines.append(f'- {step.stage}：{step.role}，{step.description}')
                if step.unlock_conditions:
                    lines.append(f'  条件：{"；".join(step.unlock_conditions)}')
                if step.missing_skills:
                    lines.append(f'  待补齐：{"、".join(step.missing_skills)}')
            lines.append('')

        lines.append('## 六、社会需求与行业发展趋势')
        lines.append(f'- 趋势快照版本：{industry_trend.snapshot_version}')
        lines.append(f'- 数据更新时间：{industry_trend.updated_at}')
        lines.append('')
        lines.append('### 岗位冷热度')
        for item in industry_trend.role_heat:
            lines.append(f'- {item.job_family}：热度 {item.heat_score}（{item.heat_level}），{item.summary}')
        lines.append('')
        lines.append('### 缺口技能热度')
        for item in industry_trend.missing_skill_trends:
            lines.append(f'- {item.skill_name}：热度 {item.heat_score}（{item.heat_level}），{item.suggestion}')
        lines.append('')
        lines.append('### 行业变化')
        for item in industry_trend.industry_shifts:
            lines.append(f'- {item.topic}：{item.summary}')
        lines.append('')
        lines.append('### 个性化建议')
        for item in industry_trend.personalized_advice:
            lines.append(f'- {item}')
        lines.append('')

        lines.append('## 七、行动计划')
        for item in action_plan:
            actions_text = '；'.join(item.actions)
            metrics_text = '；'.join(item.metrics)
            lines.append(f'### {item.phase}')
            lines.append(f'- 目标：{item.objective}')
            lines.append(f'- 行动：{actions_text}')
            lines.append(f'- 指标：{metrics_text}')
            lines.append('')

        return '\n'.join(lines)

    def _enhance_with_llm(
        self,
        student_profile: StudentProfile,
        top_matches: list[MatchResult],
        path_options: list[CareerPathOption],
        action_plan: list[ActionPlanItem],
        markdown: str,
        executive_summary: str,
        industry_trend: IndustryTrendAnalysis,
    ) -> dict:
        if self.llm_client is None or not self.llm_client.enabled:
            return {}
        prompt_payload = {
            'student_profile': student_profile.dict(),
            'top_matches': [item.dict() for item in top_matches],
            'path_options': [item.dict() for item in path_options],
            'action_plan': [item.dict() for item in action_plan],
            'industry_trend': industry_trend.dict(),
            'current_executive_summary': executive_summary,
            'current_markdown': markdown,
        }
        prompt = (
            '请在不改变事实的前提下，增强职业规划报告的表达效果，并仅返回 JSON。'
            'JSON 字段必须包含 overview、executive_summary、report_markdown。\n'
            f'{json.dumps(prompt_payload, ensure_ascii=False)}'
        )
        try:
            raw_text = self.llm_client.generate(prompt=prompt, system_prompt=REPORT_ENHANCEMENT_SYSTEM_PROMPT)
        except Exception:
            return {}
        payload = try_parse_json(raw_text)
        return payload if isinstance(payload, dict) else {}
