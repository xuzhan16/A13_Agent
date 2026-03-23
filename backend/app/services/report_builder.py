import json
from typing import Optional

from backend.app.infra.json_utils import try_parse_json
from backend.app.infra.llm.base import LLMClient
from backend.app.prompts.templates import REPORT_ENHANCEMENT_SYSTEM_PROMPT
from backend.app.schemas.job import MatchResult
from backend.app.schemas.planning import ActionPlanItem, CareerPathOption, CareerReport
from backend.app.schemas.student import StudentProfile


class ReportBuilderService:
    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm_client = llm_client

    def build(
        self,
        student_profile: StudentProfile,
        match_results: list[MatchResult],
        path_options: list[CareerPathOption],
    ) -> CareerReport:
        top_matches = match_results[:3]
        highlights = [
            f'画像完整度：{student_profile.completeness_score}',
            f'竞争力评分：{student_profile.competitiveness_score}',
        ]
        highlights.extend(
            f'{item.job_family} 匹配度 {item.overall_score}' for item in top_matches
        )
        action_plan = self._build_action_plan(top_matches)
        overview = '基于学生画像、岗位要求画像与路径图谱生成的证据驱动职业规划建议。'
        executive_summary = self._build_executive_summary(student_profile, top_matches)
        markdown = self._build_markdown(student_profile, top_matches, path_options, action_plan, executive_summary)
        generation_mode = 'template'

        enhanced = self._enhance_with_llm(
            student_profile=student_profile,
            top_matches=top_matches,
            path_options=path_options,
            action_plan=action_plan,
            markdown=markdown,
            executive_summary=executive_summary,
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
        )

    @staticmethod
    def _build_action_plan(top_matches: list[MatchResult]) -> list[ActionPlanItem]:
        primary = top_matches[0] if top_matches else None
        gaps = primary.missing_skills[:3] if primary else []

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
    def _build_executive_summary(student_profile: StudentProfile, top_matches: list[MatchResult]) -> str:
        if not top_matches:
            return '当前信息不足，建议先补齐关键经历与技能后再生成详细规划。'
        top = top_matches[0]
        strengths = '、'.join(student_profile.inferred_strengths[:2]) or '基础信息尚可'
        gaps = '、'.join(top.missing_skills[:3]) or '暂无明显关键技能缺口'
        return (
            f'当前最推荐优先冲刺“{top.job_family}”，综合匹配度为 {top.overall_score}。'
            f'你当前的主要优势在于：{strengths}；'
            f'短期内最值得补强的是：{gaps}。'
        )

    def _build_markdown(
        self,
        student_profile: StudentProfile,
        top_matches: list[MatchResult],
        path_options: list[CareerPathOption],
        action_plan: list[ActionPlanItem],
        executive_summary: str,
    ) -> str:
        hard_skills_text = '、'.join(student_profile.hard_skills) or '待补充'
        soft_skills_text = '、'.join(student_profile.soft_skills) or '待补充'
        strengths_text = '、'.join(student_profile.inferred_strengths) or '待补充'
        gaps_text = '、'.join(student_profile.inferred_gaps) or '待补充'
        lines = [
            '# 大学生职业生涯发展报告',
            '',
            '## 一、执行摘要',
            executive_summary,
            '',
            '## 二、学生画像概览',
            f'- 专业：{student_profile.basic_info.major or "待补充"}',
            f'- 完整度：{student_profile.completeness_score}',
            f'- 竞争力：{student_profile.competitiveness_score}',
            f'- 已识别硬技能：{hard_skills_text}',
            f'- 已识别软素质：{soft_skills_text}',
            f'- 主要优势：{strengths_text}',
            f'- 主要短板：{gaps_text}',
            '',
            '## 三、推荐岗位',
        ]

        for result in top_matches:
            matched_skills_text = '、'.join(result.matched_skills) or '待补充'
            missing_skills_text = '、'.join(result.missing_skills) or '无明显短板'
            lines.extend(
                [
                    f'### {result.job_family}',
                    f'- 综合匹配度：{result.overall_score}',
                    f'- 优势技能：{matched_skills_text}',
                    f'- 待补技能：{missing_skills_text}',
                    f'- 结论：{result.summary}',
                    '',
                ]
            )

        lines.append('## 四、职业路径建议')
        for option in path_options:
            lines.append(f'### {option.path_name}')
            lines.append(f'- 类型：{option.path_type}')
            lines.append(f'- 原因：{option.fit_reason}')
            for step in option.steps:
                lines.append(f'- {step.stage}：{step.role}，{step.description}')
            lines.append('')

        lines.append('## 五、行动计划')
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
    ) -> dict:
        if self.llm_client is None or not self.llm_client.enabled:
            return {}
        prompt_payload = {
            'student_profile': student_profile.dict(),
            'top_matches': [item.dict() for item in top_matches],
            'path_options': [item.dict() for item in path_options],
            'action_plan': [item.dict() for item in action_plan],
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
