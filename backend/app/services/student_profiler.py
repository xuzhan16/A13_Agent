import json
from typing import Optional

from backend.app.infra.json_utils import try_parse_json
from backend.app.infra.llm.base import LLMClient
from backend.app.prompts.templates import STUDENT_PROFILE_SYSTEM_PROMPT
from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.common import EvidenceItem
from backend.app.schemas.student import StudentIntakeRequest, StudentProfile


class StudentProfilerService:
    def __init__(
        self,
        repository: KnowledgeRepository,
        llm_client: Optional[LLMClient] = None,
    ) -> None:
        self.repository = repository
        self.llm_client = llm_client

    def build_profile(self, intake: StudentIntakeRequest) -> StudentProfile:
        corpus = self._build_corpus(intake)
        rule_hard_skills = self._extract_keywords(corpus, self.repository.get_skill_lexicon())
        rule_soft_skills = self._extract_keywords(corpus, self.repository.get_soft_skill_lexicon())
        llm_payload = self._extract_with_llm(intake)

        hard_skills = self._merge_terms(
            rule_hard_skills,
            intake.manual_skills,
            self._filter_allowed(llm_payload.get('hard_skills', []), self.repository.get_skill_lexicon()),
        )
        soft_skills = self._merge_terms(
            rule_soft_skills,
            self._filter_allowed(llm_payload.get('soft_skills', []), self.repository.get_soft_skill_lexicon()),
        )
        certificates = self._merge_terms(intake.certificates, llm_payload.get('certificates', []))

        completeness_score = self._compute_completeness(intake)
        competitiveness_score = self._compute_competitiveness(
            hard_skill_count=len(hard_skills),
            soft_skill_count=len(soft_skills),
            project_count=len(intake.project_experiences),
            internship_count=len(intake.internship_experiences),
            certificate_count=len(certificates),
        )

        inferred_strengths = self._merge_terms(
            self._build_strengths(hard_skills, soft_skills, intake),
            llm_payload.get('inferred_strengths', []),
        )
        inferred_gaps = self._merge_terms(
            self._build_gaps(hard_skills, intake),
            llm_payload.get('inferred_gaps', []),
        )
        missing_dimensions = self._build_missing_dimensions(intake, hard_skills, soft_skills, certificates)
        evidences = self._build_evidences(intake, llm_payload)
        summary = llm_payload.get('summary', '') or self._build_summary(hard_skills, soft_skills, intake)

        return StudentProfile(
            basic_info=intake.basic_info,
            preference=intake.preference,
            hard_skills=hard_skills,
            soft_skills=soft_skills,
            certificates=certificates,
            inferred_strengths=inferred_strengths,
            inferred_gaps=inferred_gaps,
            missing_dimensions=missing_dimensions,
            project_count=len(intake.project_experiences),
            internship_count=len(intake.internship_experiences),
            campus_count=len(intake.campus_experiences),
            completeness_score=completeness_score,
            competitiveness_score=competitiveness_score,
            evidences=evidences,
            profile_source='llm_augmented' if llm_payload else 'rule_based',
            summary=summary,
        )

    @staticmethod
    def _build_corpus(intake: StudentIntakeRequest) -> str:
        items = [
            intake.resume_text,
            intake.self_description,
            intake.basic_info.major,
            ' '.join(intake.manual_skills),
            ' '.join(intake.project_experiences),
            ' '.join(intake.internship_experiences),
            ' '.join(intake.campus_experiences),
            ' '.join(intake.certificates),
            ' '.join(answer.answer for answer in intake.follow_up_answers),
        ]
        return ' '.join(item for item in items if item).lower()

    @staticmethod
    def _extract_keywords(corpus: str, lexicon: list[str]) -> list[str]:
        matched = [item for item in lexicon if item.lower() in corpus]
        return sorted(set(matched))

    @staticmethod
    def _compute_completeness(intake: StudentIntakeRequest) -> float:
        parts = [
            bool(intake.resume_text.strip()),
            bool(intake.self_description.strip()),
            bool(intake.manual_skills),
            bool(intake.project_experiences),
            bool(intake.internship_experiences),
            bool(intake.campus_experiences),
            bool(intake.certificates),
            bool(intake.follow_up_answers),
        ]
        return round(sum(1 for item in parts if item) / len(parts) * 100, 1)

    @staticmethod
    def _compute_competitiveness(
        hard_skill_count: int,
        soft_skill_count: int,
        project_count: int,
        internship_count: int,
        certificate_count: int,
    ) -> float:
        raw = (
            min(hard_skill_count, 8) * 6
            + min(soft_skill_count, 4) * 5
            + min(project_count, 3) * 10
            + min(internship_count, 2) * 12
            + min(certificate_count, 3) * 6
        )
        return round(min(raw, 100), 1)

    @staticmethod
    def _build_strengths(
        hard_skills: list[str],
        soft_skills: list[str],
        intake: StudentIntakeRequest,
    ) -> list[str]:
        strengths: list[str] = []
        if hard_skills:
            strengths.append('已有较明确的技能栈基础')
        if len(intake.project_experiences) >= 1:
            strengths.append('具备项目实践经历')
        if len(intake.internship_experiences) >= 1:
            strengths.append('具备真实职场场景经历')
        if '学习能力' in soft_skills:
            strengths.append('学习与适应能力较强')
        if intake.preference.target_roles:
            strengths.append('已有较明确的岗位目标')
        return strengths or ['待进一步访谈补全优势画像']

    @staticmethod
    def _build_gaps(hard_skills: list[str], intake: StudentIntakeRequest) -> list[str]:
        gaps: list[str] = []
        if len(hard_skills) < 3:
            gaps.append('硬技能证据偏少')
        if not intake.project_experiences:
            gaps.append('缺少可展示项目经历')
        if not intake.internship_experiences:
            gaps.append('缺少实习或真实业务场景证明')
        if not intake.certificates:
            gaps.append('证书与标准化证明材料较少')
        if not intake.preference.target_roles:
            gaps.append('目标岗位尚不明确')
        return gaps

    @staticmethod
    def _build_missing_dimensions(
        intake: StudentIntakeRequest,
        hard_skills: list[str],
        soft_skills: list[str],
        certificates: list[str],
    ) -> list[str]:
        missing: list[str] = []
        if len(hard_skills) < 3:
            missing.append('硬技能')
        if len(soft_skills) < 2:
            missing.append('职业素养')
        if not intake.project_experiences:
            missing.append('项目经历')
        if not intake.internship_experiences:
            missing.append('实习经历')
        if not certificates:
            missing.append('证书证明')
        if not intake.preference.target_roles:
            missing.append('职业意向')
        if not intake.preference.target_cities:
            missing.append('城市偏好')
        return missing

    def _build_evidences(self, intake: StudentIntakeRequest, llm_payload: dict) -> list[EvidenceItem]:
        evidences: list[EvidenceItem] = []

        def add(
            source: str,
            source_type: str,
            source_ref: str,
            excerpt: str,
            normalized_value: object = '',
            confidence: float = 1.0,
            extract_rule: str = 'direct_copy',
            tags: Optional[list[str]] = None,
        ) -> None:
            text = str(excerpt).strip()
            if not text:
                return
            evidences.append(
                EvidenceItem(
                    evidence_id=f'E{len(evidences) + 1:02d}',
                    source=source,
                    source_type=source_type,
                    source_ref=source_ref,
                    excerpt=text[:220],
                    normalized_value=normalized_value,
                    confidence=confidence,
                    extract_rule=extract_rule,
                    tags=tags or [],
                )
            )

        if intake.basic_info.degree.strip():
            add(
                source='student_basic_info',
                source_type='student_basic_info',
                source_ref='basic_info.degree',
                excerpt=f'学历：{intake.basic_info.degree}',
                normalized_value=intake.basic_info.degree,
                tags=['degree'],
            )
        if intake.basic_info.major.strip():
            add(
                source='student_basic_info',
                source_type='student_basic_info',
                source_ref='basic_info.major',
                excerpt=f'专业：{intake.basic_info.major}',
                normalized_value=intake.basic_info.major,
                tags=['major'],
            )
        if intake.preference.target_roles:
            add(
                source='student_preference',
                source_type='student_preference',
                source_ref='preference.target_roles',
                excerpt=f'目标岗位：{"、".join(intake.preference.target_roles)}',
                normalized_value=intake.preference.target_roles,
                tags=['target_role'],
            )
        if intake.preference.target_cities:
            add(
                source='student_preference',
                source_type='student_preference',
                source_ref='preference.target_cities',
                excerpt=f'目标城市：{"、".join(intake.preference.target_cities)}',
                normalized_value=intake.preference.target_cities,
                tags=['target_city'],
            )
        if intake.resume_text.strip():
            add(
                source='resume_text',
                source_type='resume_text',
                source_ref='resume_text',
                excerpt=intake.resume_text,
                normalized_value=intake.resume_text[:160],
                extract_rule='resume_segment',
                tags=['resume'],
            )
        if intake.self_description.strip():
            add(
                source='self_description',
                source_type='self_description',
                source_ref='self_description',
                excerpt=intake.self_description,
                normalized_value=intake.self_description[:160],
                extract_rule='self_report',
                tags=['self_description'],
            )
        if intake.manual_skills:
            add(
                source='manual_skills',
                source_type='manual_skills',
                source_ref='manual_skills',
                excerpt=f'手动技能：{"、".join(intake.manual_skills)}',
                normalized_value=intake.manual_skills,
                extract_rule='manual_input',
                tags=['skill', 'manual_skill'],
            )
        for index, item in enumerate(intake.project_experiences, start=1):
            add(
                source='project',
                source_type='project_experience',
                source_ref=f'project_experiences[{index - 1}]',
                excerpt=item,
                normalized_value=item[:160],
                extract_rule='project_segment',
                tags=['project'],
            )
        for index, item in enumerate(intake.internship_experiences, start=1):
            add(
                source='internship',
                source_type='internship_experience',
                source_ref=f'internship_experiences[{index - 1}]',
                excerpt=item,
                normalized_value=item[:160],
                extract_rule='internship_segment',
                tags=['internship'],
            )
        for index, item in enumerate(intake.campus_experiences, start=1):
            add(
                source='campus',
                source_type='campus_experience',
                source_ref=f'campus_experiences[{index - 1}]',
                excerpt=item,
                normalized_value=item[:160],
                extract_rule='campus_segment',
                tags=['campus'],
            )
        if intake.certificates:
            add(
                source='certificates',
                source_type='certificate',
                source_ref='certificates',
                excerpt=f'证书：{"、".join(intake.certificates)}',
                normalized_value=intake.certificates,
                extract_rule='certificate_list',
                tags=['certificate'],
            )
        for index, item in enumerate(intake.follow_up_answers, start=1):
            add(
                source='follow_up',
                source_type='follow_up_answer',
                source_ref=f'follow_up_answers[{index - 1}]',
                excerpt=f'{item.question}：{item.answer}',
                normalized_value={'question': item.question, 'answer': item.answer},
                confidence=0.95,
                extract_rule='follow_up_capture',
                tags=['follow_up'],
            )
        for item in llm_payload.get('evidences', [])[:2]:
            if isinstance(item, str) and item.strip():
                add(
                    source='llm_extracted',
                    source_type='llm_extracted',
                    source_ref='llm_payload.evidences',
                    excerpt=item,
                    normalized_value=item[:160],
                    confidence=0.72,
                    extract_rule='llm_extract',
                    tags=['llm'],
                )
        return evidences

    @staticmethod
    def _build_summary(
        hard_skills: list[str],
        soft_skills: list[str],
        intake: StudentIntakeRequest,
    ) -> str:
        return (
            f'当前已识别 {len(hard_skills)} 项硬技能、{len(soft_skills)} 项软素质，'
            f'包含 {len(intake.project_experiences)} 段项目经历和 {len(intake.internship_experiences)} 段实习经历。'
        )

    @staticmethod
    def _merge_terms(*groups: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for group in groups:
            for item in group:
                text = str(item).strip()
                if not text or text in seen:
                    continue
                seen.add(text)
                result.append(text)
        return result

    @staticmethod
    def _filter_allowed(items: list[str], allowed_terms: list[str]) -> list[str]:
        allowed = {item.lower(): item for item in allowed_terms}
        result: list[str] = []
        for item in items:
            normalized = str(item).strip().lower()
            if normalized in allowed:
                result.append(allowed[normalized])
        return result

    def _extract_with_llm(self, intake: StudentIntakeRequest) -> dict:
        if self.llm_client is None or not self.llm_client.enabled:
            return {}

        prompt = self._build_llm_prompt(intake)
        try:
            raw_text = self.llm_client.generate(prompt=prompt, system_prompt=STUDENT_PROFILE_SYSTEM_PROMPT)
        except Exception:
            return {}

        payload = try_parse_json(raw_text)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _build_llm_prompt(intake: StudentIntakeRequest) -> str:
        payload = {
            'basic_info': intake.basic_info.dict(),
            'preference': intake.preference.dict(),
            'resume_text': intake.resume_text,
            'self_description': intake.self_description,
            'manual_skills': intake.manual_skills,
            'project_experiences': intake.project_experiences,
            'internship_experiences': intake.internship_experiences,
            'campus_experiences': intake.campus_experiences,
            'certificates': intake.certificates,
            'follow_up_answers': [item.dict() for item in intake.follow_up_answers],
        }
        return (
            '请从以下学生资料中抽取结构化画像，并仅返回 JSON。'
            'JSON 字段必须包含 hard_skills、soft_skills、certificates、inferred_strengths、inferred_gaps、evidences、summary。\n'
            f'{json.dumps(payload, ensure_ascii=False)}'
        )
