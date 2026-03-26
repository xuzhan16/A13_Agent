import json
from typing import Optional

from backend.app.infra.json_utils import try_parse_json
from backend.app.infra.llm.base import LLMClient
from backend.app.prompts.templates import STUDENT_PROFILE_SYSTEM_PROMPT
from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.common import EvidenceItem, SoftSkillAssessment
from backend.app.schemas.student import StudentIntakeRequest, StudentProfile
from backend.app.services.soft_skill_assessor import SoftSkillAssessmentService


class StudentProfilerService:
    def __init__(
        self,
        repository: KnowledgeRepository,
        soft_skill_assessor: SoftSkillAssessmentService,
        llm_client: Optional[LLMClient] = None,
    ) -> None:
        self.repository = repository
        self.soft_skill_assessor = soft_skill_assessor
        self.llm_client = llm_client

    def build_profile(self, intake: StudentIntakeRequest) -> StudentProfile:
        corpus = self._build_corpus(intake)
        rule_hard_skills = self._extract_keywords(corpus, self.repository.get_skill_lexicon())
        llm_payload = self._extract_with_llm(intake)

        hard_skills = self._merge_terms(
            rule_hard_skills,
            intake.manual_skills,
            self._filter_allowed(llm_payload.get('hard_skills', []), self.repository.get_skill_lexicon()),
        )
        certificates = self._merge_terms(intake.certificates, llm_payload.get('certificates', []))
        evidences = self._build_evidences(intake, llm_payload)
        soft_skill_assessments = self.soft_skill_assessor.assess(intake, hard_skills, evidences)

        rule_soft_skills = self._extract_keywords(corpus, self.repository.get_soft_skill_lexicon())
        assessment_labels = self.soft_skill_assessor.labels_from_assessments(soft_skill_assessments)
        soft_skills = self._merge_terms(
            rule_soft_skills,
            assessment_labels,
            self._filter_soft_skills(llm_payload.get('soft_skills', []), assessment_labels),
        )

        completeness_score = self._compute_completeness(intake)
        competitiveness_score = self._compute_competitiveness(
            hard_skill_count=len(hard_skills),
            soft_skill_count=len(soft_skills),
            project_count=len(intake.project_experiences),
            internship_count=len(intake.internship_experiences),
            certificate_count=len(certificates),
            soft_skill_assessments=soft_skill_assessments,
        )

        inferred_strengths = self._merge_terms(
            self._build_strengths(hard_skills, soft_skill_assessments, intake),
            llm_payload.get('inferred_strengths', []),
        )
        inferred_gaps = self._merge_terms(
            self._build_gaps(hard_skills, soft_skill_assessments, intake),
            llm_payload.get('inferred_gaps', []),
        )
        missing_dimensions = self._build_missing_dimensions(intake, hard_skills, soft_skills, certificates)
        summary = llm_payload.get('summary', '') or self._build_summary(hard_skills, soft_skill_assessments, intake)

        return StudentProfile(
            basic_info=intake.basic_info,
            preference=intake.preference,
            hard_skills=hard_skills,
            soft_skills=soft_skills,
            soft_skill_assessments=soft_skill_assessments,
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
        soft_skill_assessments: list[SoftSkillAssessment],
    ) -> float:
        soft_bonus = 0.0
        if soft_skill_assessments:
            soft_bonus = sum(item.score for item in soft_skill_assessments) / len(soft_skill_assessments) * 0.15
        raw = (
            min(hard_skill_count, 8) * 6
            + min(soft_skill_count, 5) * 4
            + min(project_count, 3) * 10
            + min(internship_count, 2) * 12
            + min(certificate_count, 3) * 6
            + soft_bonus
        )
        return round(min(raw, 100), 1)

    @staticmethod
    def _build_strengths(
        hard_skills: list[str],
        soft_skill_assessments: list[SoftSkillAssessment],
        intake: StudentIntakeRequest,
    ) -> list[str]:
        strengths: list[str] = []
        if hard_skills:
            strengths.append('\u5df2\u6709\u8f83\u660e\u786e\u7684\u6280\u80fd\u6808\u57fa\u7840')
        if len(intake.project_experiences) >= 1:
            strengths.append('\u5177\u5907\u9879\u76ee\u5b9e\u8df5\u7ecf\u5386')
        if len(intake.internship_experiences) >= 1:
            strengths.append('\u5df2\u6709\u8f83\u660e\u786e\u7684\u5c97\u4f4d\u76ee\u6807')
        if intake.preference.target_roles:
            strengths.append('\u5df2\u6709\u8f83\u660e\u786e\u7684\u5c97\u4f4d\u76ee\u6807')

        ranked = sorted(soft_skill_assessments, key=lambda item: item.score, reverse=True)
        for item in ranked[:2]:
            if item.score >= 75:
                strengths.append(f'{item.skill_name}\u8868\u73b0\u8f83\u5f3a')
        return strengths or ['\u5f85\u8fdb\u4e00\u6b65\u8bbf\u8c08\u8865\u5168\u4f18\u52bf\u753b\u50cf']

    @staticmethod
    def _build_gaps(
        hard_skills: list[str],
        soft_skill_assessments: list[SoftSkillAssessment],
        intake: StudentIntakeRequest,
    ) -> list[str]:
        gaps: list[str] = []
        if len(hard_skills) < 3:
            gaps.append('\u786c\u6280\u80fd\u8bc1\u636e\u504f\u5c11')
        if not intake.project_experiences:
            gaps.append('\u7f3a\u5c11\u53ef\u5c55\u793a\u9879\u76ee\u7ecf\u5386')
        if not intake.internship_experiences:
            gaps.append('\u7f3a\u5c11\u5b9e\u4e60\u6216\u771f\u5b9e\u4e1a\u52a1\u573a\u666f\u8bc1\u660e')
        if not intake.certificates:
            gaps.append('\u8bc1\u4e66\u4e0e\u6807\u51c6\u5316\u8bc1\u660e\u6750\u6599\u8f83\u5c11')
        if not intake.preference.target_roles:
            gaps.append('\u76ee\u6807\u5c97\u4f4d\u5c1a\u4e0d\u660e\u786e')
        for item in sorted(soft_skill_assessments, key=lambda row: row.score)[:2]:
            if item.score < 62:
                gaps.append(f'{item.skill_name}\u8bc1\u636e\u8f83\u5f31')
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
            missing.append('\u786c\u6280\u80fd')
        if len(soft_skills) < 2:
            missing.append('\u57ce\u5e02\u504f\u597d')
        if not intake.project_experiences:
            missing.append('\u57ce\u5e02\u504f\u597d')
        if not intake.internship_experiences:
            missing.append('\u57ce\u5e02\u504f\u597d')
        if not certificates:
            missing.append('\u57ce\u5e02\u504f\u597d')
        if not intake.preference.target_roles:
            missing.append('\u57ce\u5e02\u504f\u597d')
        if not intake.preference.target_cities:
            missing.append('\u57ce\u5e02\u504f\u597d')
        return missing

    def _build_evidences(self, intake: StudentIntakeRequest, llm_payload: dict) -> list[EvidenceItem]:
        evidences: list[EvidenceItem] = []
        sep = '\u3001'

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
                excerpt=f'\u5b66\u5386\uff1a{intake.basic_info.degree}',
                normalized_value=intake.basic_info.degree,
                tags=['degree'],
            )
        if intake.basic_info.major.strip():
            add(
                source='student_basic_info',
                source_type='student_basic_info',
                source_ref='basic_info.major',
                excerpt=f'\u4e13\u4e1a\uff1a{intake.basic_info.major}',
                normalized_value=intake.basic_info.major,
                tags=['major'],
            )
        if intake.preference.target_roles:
            add(
                source='student_preference',
                source_type='student_preference',
                source_ref='preference.target_roles',
                excerpt=f'\u76ee\u6807\u5c97\u4f4d\uff1a{sep.join(intake.preference.target_roles)}',
                normalized_value=intake.preference.target_roles,
                tags=['target_role'],
            )
        if intake.preference.target_cities:
            add(
                source='student_preference',
                source_type='student_preference',
                source_ref='preference.target_cities',
                excerpt=f'\u76ee\u6807\u57ce\u5e02\uff1a{sep.join(intake.preference.target_cities)}',
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
                excerpt=f'\u624b\u52a8\u6280\u80fd\uff1a{sep.join(intake.manual_skills)}',
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
                excerpt=f'\u8bc1\u4e66\uff1a{sep.join(intake.certificates)}',
                normalized_value=intake.certificates,
                extract_rule='certificate_list',
                tags=['certificate'],
            )
        for index, item in enumerate(intake.follow_up_answers, start=1):
            add(
                source='follow_up',
                source_type='follow_up_answer',
                source_ref=f'follow_up_answers[{index - 1}]',
                excerpt=f'{item.question}\uff1a{item.answer}',
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
        soft_skill_assessments: list[SoftSkillAssessment],
        intake: StudentIntakeRequest,
    ) -> str:
        top_soft = max(soft_skill_assessments, key=lambda item: item.score).skill_name if soft_skill_assessments else '\u804c\u4e1a\u7d20\u517b'
        return (
            f'\u5f53\u524d\u5df2\u8bc6\u522b {len(hard_skills)} \u9879\u786c\u6280\u80fd\uff0c\u5305\u542b {len(intake.project_experiences)} \u6bb5\u9879\u76ee\u7ecf\u5386\u548c {len(intake.internship_experiences)} \u6bb5\u5b9e\u4e60\u7ecf\u5386\u3002'
            f'\u8f6f\u7d20\u8d28\u4e2d\u8868\u73b0\u6700\u7a81\u51fa\u7684\u7ef4\u5ea6\u662f\uff1a{top_soft}\u3002'
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

    @staticmethod
    def _filter_soft_skills(items: list[str], assessment_labels: list[str]) -> list[str]:
        candidate_map = {label.lower(): label for label in assessment_labels}
        candidate_map.update({
            '\u56e2\u961f\u534f\u4f5c': '\u56e2\u961f\u534f\u4f5c',
            '\u56e2\u961f\u534f\u4f5c': '\u56e2\u961f\u534f\u4f5c',
            '\u56e2\u961f\u534f\u4f5c': '\u56e2\u961f\u534f\u4f5c',
            '\u6267\u884c\u529b': '\u6267\u884c\u529b',
            '\u56e2\u961f\u534f\u4f5c': '\u56e2\u961f\u534f\u4f5c',
            '\u56e2\u961f\u534f\u4f5c': '\u56e2\u961f\u534f\u4f5c',
        })
        result: list[str] = []
        for item in items:
            text = str(item).strip()
            if text in candidate_map.values():
                result.append(text)
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
            '\u8bf7\u4ece\u4ee5\u4e0b\u5b66\u751f\u8d44\u6599\u4e2d\u62bd\u53d6\u7ed3\u6784\u5316\u753b\u50cf\uff0c\u5e76\u4ec5\u8fd4\u56de JSON\u3002'
            'JSON \u5b57\u6bb5\u5fc5\u987b\u5305\u542b hard_skills\u3001soft_skills\u3001certificates\u3001inferred_strengths\u3001inferred_gaps\u3001evidences\u3001summary\u3002\n'
            f'{json.dumps(payload, ensure_ascii=False)}'
        )
