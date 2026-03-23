import json
from typing import Optional

from backend.app.infra.json_utils import try_parse_json
from backend.app.infra.llm.base import LLMClient
from backend.app.prompts.templates import FOLLOW_UP_QUESTION_SYSTEM_PROMPT
from backend.app.schemas.job import MatchResult
from backend.app.schemas.planning import FollowUpQuestion
from backend.app.schemas.student import StudentIntakeRequest, StudentProfile


class FollowUpQuestionService:
    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm_client = llm_client

    def generate(
        self,
        intake: StudentIntakeRequest,
        student_profile: StudentProfile,
        match_results: list[MatchResult],
        max_questions: int = 4,
    ) -> list[FollowUpQuestion]:
        rule_questions = self._generate_rule_based(intake, student_profile, match_results)
        llm_questions = self._generate_with_llm(intake, student_profile, match_results, max_questions)

        merged: list[FollowUpQuestion] = []
        seen: set[str] = set()
        for item in llm_questions + rule_questions:
            key = item.question.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(item)
            if len(merged) >= max_questions:
                break
        return merged

    def _generate_rule_based(
        self,
        intake: StudentIntakeRequest,
        student_profile: StudentProfile,
        match_results: list[MatchResult],
    ) -> list[FollowUpQuestion]:
        questions: list[FollowUpQuestion] = []
        if not intake.preference.target_roles:
            questions.append(
                FollowUpQuestion(
                    question_id='career_goal',
                    question='你当前最希望优先投递的岗位方向是什么？如果要排优先级，请给出前 2 个。',
                    reason='目标岗位不明确会直接影响岗位匹配和路径规划。',
                    priority=1,
                )
            )
        if not intake.preference.target_cities:
            questions.append(
                FollowUpQuestion(
                    question_id='target_city',
                    question='你更希望在哪些城市就业？是否接受异地实习或校招调剂？',
                    reason='城市偏好会影响岗位推荐范围与行动计划。',
                    priority=1,
                )
            )
        if not intake.project_experiences:
            questions.append(
                FollowUpQuestion(
                    question_id='project_experience',
                    question='请补充 1 到 2 段最能代表你能力的项目经历，并说明你负责的模块和结果。',
                    reason='项目经历是应届生证明硬技能最重要的证据之一。',
                    priority=1,
                )
            )
        if not intake.internship_experiences:
            questions.append(
                FollowUpQuestion(
                    question_id='internship_experience',
                    question='你是否有实习、驻场、科研助研或兼职开发经历？请补充最接近职场场景的一段。',
                    reason='真实业务场景经历有助于提升发展潜力评分。',
                    priority=2,
                )
            )
        if not intake.certificates:
            questions.append(
                FollowUpQuestion(
                    question_id='certificate',
                    question='你是否有英语、软考、计算机等级、PMP、ISTQB 等证书或标准化证明？',
                    reason='证书能补充简历中的可信证明材料。',
                    priority=3,
                )
            )
        if len(student_profile.hard_skills) < 3:
            questions.append(
                FollowUpQuestion(
                    question_id='core_skills',
                    question='请列出你最熟练的 3 到 5 项技术技能，以及每项技能分别用在什么项目里。',
                    reason='当前可识别的硬技能证据不足，需要进一步澄清技能栈。',
                    priority=1,
                )
            )
        if match_results:
            top = match_results[0]
            if top.missing_skills:
                questions.append(
                    FollowUpQuestion(
                        question_id='gap_confirmation',
                        question=f'针对目标岗位“{top.job_family}”，你是否已有 {"、".join(top.missing_skills[:3])} 相关经历或学习计划？',
                        reason='确认关键差距项是否真的缺失，有助于提升匹配准确性。',
                        priority=2,
                    )
                )
        if not intake.follow_up_answers:
            questions.append(
                FollowUpQuestion(
                    question_id='work_style',
                    question='你更偏好稳定执行型工作、技术探索型工作，还是客户沟通/项目推进型工作？为什么？',
                    reason='工作风格会影响职业路径和备选岗位建议。',
                    priority=2,
                )
            )
        return questions

    def _generate_with_llm(
        self,
        intake: StudentIntakeRequest,
        student_profile: StudentProfile,
        match_results: list[MatchResult],
        max_questions: int,
    ) -> list[FollowUpQuestion]:
        if self.llm_client is None or not self.llm_client.enabled:
            return []
        prompt_payload = {
            'basic_info': intake.basic_info.dict(),
            'preference': intake.preference.dict(),
            'student_profile': student_profile.dict(),
            'top_matches': [item.dict() for item in match_results[:3]],
            'max_questions': max_questions,
        }
        prompt = (
            '请根据当前学生画像和匹配结果，生成需要继续追问的高价值问题，并仅返回 JSON 数组。'
            '每个对象必须包含 question_id、question、reason、priority。\n'
            f'{json.dumps(prompt_payload, ensure_ascii=False)}'
        )
        try:
            raw_text = self.llm_client.generate(prompt=prompt, system_prompt=FOLLOW_UP_QUESTION_SYSTEM_PROMPT)
        except Exception:
            return []

        payload = try_parse_json(raw_text)
        if not isinstance(payload, list):
            return []

        questions: list[FollowUpQuestion] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            try:
                questions.append(FollowUpQuestion(**item))
            except Exception:
                continue
        return questions[:max_questions]
