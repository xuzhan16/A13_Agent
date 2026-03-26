from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional

from backend.app.schemas.common import EvidenceItem, IndicatorScore, ScoreDeduction, SoftSkillAssessment
from backend.app.schemas.student import StudentIntakeRequest


@dataclass(frozen=True)
class SoftSkillRule:
    skill_code: str
    skill_name: str
    suggestions: tuple[str, ...]


class SoftSkillAssessmentService:
    RULES: tuple[SoftSkillRule, ...] = (
        SoftSkillRule(
            skill_code='innovation',
            skill_name='\u521b\u65b0\u80fd\u529b',
            suggestions=(
                '\u8865\u5145\u9879\u76ee\u521b\u65b0\u70b9\u7684\u6280\u672f\u96be\u70b9\u4e0e\u53d6\u820d',
                '\u8865\u5145\u7ade\u8d5b\u3001\u8f6f\u8457\u3001\u4e13\u5229\u7b49\u5916\u90e8\u8bc1\u660e',
                '\u628a\u521b\u65b0\u65b9\u6848\u7684\u91cf\u5316\u7ed3\u679c\u5199\u8fdb\u7b80\u5386',
            ),
        ),
        SoftSkillRule(
            skill_code='communication',
            skill_name='\u6c9f\u901a\u80fd\u529b',
            suggestions=(
                '\u8865\u5145\u8de8\u89d2\u8272\u534f\u4f5c\u4e0e\u8054\u8c03\u7ecf\u5386',
                '\u589e\u52a0\u6c47\u62a5\u3001\u7b54\u8fa9\u3001\u5206\u4eab\u7b49\u8868\u8fbe\u8bc1\u636e',
                '\u660e\u786e\u4f60\u4e0e\u4ea7\u54c1\u3001\u6d4b\u8bd5\u3001\u5ba2\u6237\u7684\u6c9f\u901a\u7ed3\u679c',
            ),
        ),
        SoftSkillRule(
            skill_code='stress_tolerance',
            skill_name='\u6297\u538b\u80fd\u529b',
            suggestions=(
                '\u8865\u5145 deadline\u3001\u5e76\u884c\u4efb\u52a1\u6216\u6545\u969c\u6392\u67e5\u573a\u666f',
                '\u7a81\u51fa\u6301\u7eed\u6295\u5165\u548c\u9ad8\u538b\u4e0b\u4ea4\u4ed8\u7ed3\u679c',
                '\u8865\u5145\u95ee\u9898\u6062\u590d\u4e0e\u590d\u76d8\u8fc7\u7a0b',
            ),
        ),
        SoftSkillRule(
            skill_code='learning_agility',
            skill_name='\u5b66\u4e60\u80fd\u529b',
            suggestions=(
                '\u8865\u5145\u81ea\u5b66\u8def\u5f84\u548c\u5b66\u4e60\u8282\u594f',
                '\u5f3a\u8c03\u201c\u5b66\u4e86\u4ec0\u4e48\uff0c\u5982\u4f55\u7528\u5230\u9879\u76ee\u91cc\u201d',
                '\u589e\u52a0\u8bc1\u4e66\u3001\u535a\u5ba2\u3001\u6280\u672f\u7b14\u8bb0\u7b49\u6301\u7eed\u6210\u957f\u8bc1\u636e',
            ),
        ),
        SoftSkillRule(
            skill_code='execution',
            skill_name='\u6267\u884c\u529b',
            suggestions=(
                '\u8865\u5145\u5b8c\u6574\u4ea4\u4ed8\u95ed\u73af\u548c\u65f6\u95f4\u8282\u70b9',
                '\u7a81\u51fa\u91cf\u5316\u7ed3\u679c\u4e0e\u4e1a\u52a1\u5f71\u54cd',
                '\u660e\u786e\u4f60\u8d1f\u8d23\u7684\u6a21\u5757\u548c\u5b8c\u6210\u7ed3\u679c',
            ),
        ),
    )

    QUANTIFIED_PATTERN = re.compile('(\u63d0\u5347|\u4e0b\u964d|\u51cf\u5c11|\u7f29\u77ed|\u589e\u957f|\u4f18\u5316|\u964d\u4f4e|\u63d0\u9ad8).{0,8}(\\d+%|\\d+ms|\\d+\u79d2|\\d+\u5929|\\d+\u4e2a)')

    def assess(
        self,
        intake: StudentIntakeRequest,
        hard_skills: list[str],
        evidences: list[EvidenceItem],
    ) -> list[SoftSkillAssessment]:
        return [
            self._score_innovation(intake, evidences),
            self._score_communication(evidences),
            self._score_stress_tolerance(intake, evidences),
            self._score_learning_agility(intake, hard_skills, evidences),
            self._score_execution(intake, evidences),
        ]

    @staticmethod
    def labels_from_assessments(assessments: list[SoftSkillAssessment], threshold: float = 68.0) -> list[str]:
        return [item.skill_name for item in assessments if item.score >= threshold]

    def _score_innovation(self, intake: StudentIntakeRequest, evidences: list[EvidenceItem]) -> SoftSkillAssessment:
        novelty_keywords = ['\u521b\u65b0', '\u4f18\u5316', '\u6539\u8fdb', '\u81ea\u7814', '\u8bbe\u8ba1', '\u9996\u6b21', '\u4ece0\u52301', '\u65b0\u65b9\u6848', '\u63a8\u8350']
        validation_keywords = ['\u83b7\u5956', '\u4e00\u7b49\u5956', '\u4e8c\u7b49\u5956', '\u4e09\u7b49\u5956', '\u4e13\u5229', '\u8f6f\u8457', '\u8bba\u6587', '\u53d1\u8868', '\u521b\u4e1a']
        breakthrough_keywords = ['\u67b6\u6784', '\u6027\u80fd', '\u7f13\u5b58', '\u63a8\u8350', '\u81ea\u52a8\u5316', '\u6a21\u578b', '\u7cfb\u7edf\u8bbe\u8ba1']

        novelty = self._make_indicator(
            skill_code='innovation',
            code='novelty',
            name='\u65b0\u9896\u6027',
            weight=0.30,
            score=min(100.0, 35 + self._keyword_hits(evidences, novelty_keywords, tags=['project', 'internship', 'campus', 'resume']) * 11 + self._pattern_hits(evidences, ['\u4ece0\u52301', '\u9996\u6b21', '\u81ea\u7814', '\u8bbe\u8ba1.+\u65b9\u6848']) * 10),
            formula='35 + innovation_hits*11 + pattern_hits*10',
            raw_value={'keywords': novelty_keywords},
            evidence_refs=self._find_evidence_refs(evidences, keywords=novelty_keywords, tags=['project', 'internship', 'campus', 'resume']),
        )
        validation_hits = self._keyword_hits(evidences, validation_keywords, tags=['project', 'campus', 'certificate', 'resume'])
        validation = self._make_indicator(
            skill_code='innovation',
            code='validation',
            name='\u6210\u679c\u9a8c\u8bc1',
            weight=0.25,
            score=min(100.0, 25 + validation_hits * 20),
            formula='25 + validation_hits*20',
            raw_value={'validation_hits': validation_hits},
            evidence_refs=self._find_evidence_refs(evidences, keywords=validation_keywords, tags=['project', 'campus', 'certificate', 'resume']),
            deductions=[ScoreDeduction(reason='\u7f3a\u5c11\u5916\u90e8\u8ba4\u53ef\u6216\u6210\u679c\u56fa\u5316\u8bc1\u660e', delta=-18)] if validation_hits == 0 else [],
        )
        quantified_hits = self._quantified_hits(evidences, tags=['project', 'internship', 'resume'])
        delivery = self._make_indicator(
            skill_code='innovation',
            code='delivery_conversion',
            name='\u843d\u5730\u8f6c\u5316',
            weight=0.25,
            score=min(100.0, 30 + quantified_hits * 18 + len(intake.project_experiences) * 6),
            formula='30 + quantified_hits*18 + project_count*6',
            raw_value={'quantified_hits': quantified_hits, 'project_count': len(intake.project_experiences)},
            evidence_refs=self._find_quantified_refs(evidences, tags=['project', 'internship', 'resume']),
            deductions=[ScoreDeduction(reason='\u521b\u65b0\u7ed3\u679c\u7f3a\u5c11\u91cf\u5316\u6307\u6807\u652f\u6491', delta=-16)] if quantified_hits == 0 else [],
        )
        breakthrough = self._make_indicator(
            skill_code='innovation',
            code='technical_breakthrough',
            name='\u6280\u672f\u7a81\u7834',
            weight=0.20,
            score=min(100.0, 38 + self._keyword_hits(evidences, breakthrough_keywords, tags=['project', 'internship', 'resume']) * 12),
            formula='38 + breakthrough_hits*12',
            raw_value={'keywords': breakthrough_keywords},
            evidence_refs=self._find_evidence_refs(evidences, keywords=breakthrough_keywords, tags=['project', 'internship', 'resume']),
        )
        return self._finalize_assessment(self._rule_by_code('innovation'), [novelty, validation, delivery, breakthrough])

    def _score_communication(self, evidences: list[EvidenceItem]) -> SoftSkillAssessment:
        teamwork_keywords = ['\u56e2\u961f', '\u534f\u4f5c', '\u5408\u4f5c', '\u8054\u8c03', '\u7ec4\u7ec7', '\u534f\u8c03']
        cross_role_keywords = ['\u5ba2\u6237', '\u4ea7\u54c1', '\u6d4b\u8bd5', '\u524d\u7aef', '\u540e\u7aef', '\u8de8\u90e8\u95e8', '\u5bf9\u63a5']
        presentation_keywords = ['\u6c47\u62a5', '\u5206\u4eab', '\u7b54\u8fa9', '\u4e3b\u6301', '\u57f9\u8bad', '\u6c9f\u901a']
        documentation_keywords = ['\u6587\u6863', '\u8bf4\u660e', '\u62a5\u544a', '\u9700\u6c42', '\u603b\u7ed3']

        teamwork = self._make_indicator('communication', 'teamwork', '\u56e2\u961f\u534f\u4f5c', 0.35, min(100.0, 40 + self._keyword_hits(evidences, teamwork_keywords, tags=['project', 'internship', 'campus']) * 12), '40 + teamwork_hits*12', {'keywords': teamwork_keywords}, self._find_evidence_refs(evidences, keywords=teamwork_keywords, tags=['project', 'internship', 'campus']))
        cross_refs = self._find_evidence_refs(evidences, keywords=cross_role_keywords, tags=['project', 'internship', 'follow_up'])
        cross_role = self._make_indicator('communication', 'cross_role', '\u8de8\u89d2\u8272\u6c9f\u901a', 0.25, min(100.0, 35 + self._keyword_hits(evidences, cross_role_keywords, tags=['project', 'internship', 'follow_up']) * 15), '35 + cross_role_hits*15', {'keywords': cross_role_keywords}, cross_refs, deductions=[ScoreDeduction(reason='\u7f3a\u5c11\u4e0e\u4ea7\u54c1\u3001\u6d4b\u8bd5\u3001\u5ba2\u6237\u7b49\u89d2\u8272\u534f\u540c\u8bc1\u636e', delta=-15)] if not cross_refs else [])
        presentation = self._make_indicator('communication', 'presentation', '\u6c47\u62a5\u8868\u8fbe', 0.20, min(100.0, 35 + self._keyword_hits(evidences, presentation_keywords, tags=['campus', 'follow_up', 'self_description']) * 16), '35 + presentation_hits*16', {'keywords': presentation_keywords}, self._find_evidence_refs(evidences, keywords=presentation_keywords, tags=['campus', 'follow_up', 'self_description']))
        documentation = self._make_indicator('communication', 'documentation', '\u6587\u6863\u6c89\u6dc0', 0.20, min(100.0, 35 + self._keyword_hits(evidences, documentation_keywords, tags=['project', 'internship', 'campus', 'resume']) * 14), '35 + doc_hits*14', {'keywords': documentation_keywords}, self._find_evidence_refs(evidences, keywords=documentation_keywords, tags=['project', 'internship', 'campus', 'resume']))
        return self._finalize_assessment(self._rule_by_code('communication'), [teamwork, cross_role, presentation, documentation])

    def _score_stress_tolerance(self, intake: StudentIntakeRequest, evidences: list[EvidenceItem]) -> SoftSkillAssessment:
        pressure_keywords = ['deadline', '\u4e0a\u7ebf', '\u7d27\u6025', '\u653b\u575a', '\u9ad8\u538b', '\u5e76\u884c', '\u6311\u6218', '\u590d\u6742']
        duration_keywords = ['\u8fde\u7eed', '\u957f\u671f', '\u6bcf\u5468', '\u9a7b\u573a', '\u5b9e\u4e60', '\u9879\u76ee']
        complexity_keywords = ['\u9ad8\u5e76\u53d1', '\u6027\u80fd', '\u6545\u969c', '\u6392\u67e5', '\u5b9a\u4f4d', '\u517c\u5bb9', '\u538b\u6d4b']
        recovery_keywords = ['\u89e3\u51b3', '\u4fee\u590d', '\u95ed\u73af', '\u6062\u590d', '\u4f18\u5316']

        pressure_scene = self._make_indicator('stress_tolerance', 'pressure_scene', '\u9ad8\u538b\u573a\u666f', 0.30, min(100.0, 35 + self._keyword_hits(evidences, pressure_keywords, tags=['project', 'internship', 'resume', 'follow_up']) * 14), '35 + pressure_hits*14', {'keywords': pressure_keywords}, self._find_evidence_refs(evidences, keywords=pressure_keywords, tags=['project', 'internship', 'resume', 'follow_up']))
        duration_bonus = len(intake.internship_experiences) * 14 + len(intake.project_experiences) * 8
        sustained = self._make_indicator('stress_tolerance', 'sustained_input', '\u6301\u7eed\u6295\u5165', 0.25, min(100.0, 30 + duration_bonus + self._keyword_hits(evidences, duration_keywords, tags=['internship', 'project', 'resume']) * 8), '30 + duration_bonus + duration_hits*8', {'internship_count': len(intake.internship_experiences), 'project_count': len(intake.project_experiences)}, self._find_evidence_refs(evidences, keywords=duration_keywords, tags=['internship', 'project', 'resume']))
        complexity = self._make_indicator('stress_tolerance', 'complexity', '\u590d\u6742\u4efb\u52a1\u5904\u7406', 0.25, min(100.0, 35 + self._keyword_hits(evidences, complexity_keywords, tags=['project', 'internship', 'resume']) * 13), '35 + complexity_hits*13', {'keywords': complexity_keywords}, self._find_evidence_refs(evidences, keywords=complexity_keywords, tags=['project', 'internship', 'resume']))
        recovery = self._make_indicator('stress_tolerance', 'recovery', '\u95ee\u9898\u6062\u590d\u529b', 0.20, min(100.0, 32 + self._keyword_hits(evidences, recovery_keywords, tags=['project', 'internship', 'resume']) * 14), '32 + recovery_hits*14', {'keywords': recovery_keywords}, self._find_evidence_refs(evidences, keywords=recovery_keywords, tags=['project', 'internship', 'resume']))
        return self._finalize_assessment(self._rule_by_code('stress_tolerance'), [pressure_scene, sustained, complexity, recovery])

    def _score_learning_agility(self, intake: StudentIntakeRequest, hard_skills: list[str], evidences: list[EvidenceItem]) -> SoftSkillAssessment:
        breadth_keywords = ['\u8de8\u9886\u57df', '\u524d\u7aef', '\u540e\u7aef', '\u6d4b\u8bd5', '\u7b97\u6cd5', '\u6570\u636e\u5e93', '\u90e8\u7f72']
        speed_keywords = ['\u81ea\u5b66', '\u5feb\u901f\u4e0a\u624b', '\u5b66\u4e60', '\u638c\u63e1', '\u7814\u7a76', '\u5237\u9898', '\u7b14\u8bb0']
        transfer_keywords = ['\u5e94\u7528', '\u5b9e\u73b0', '\u843d\u5730', '\u7528\u4e8e', '\u8fc1\u79fb', '\u5b9e\u8df5']
        growth_keywords = ['\u8bc1\u4e66', '\u8bfe\u7a0b', '\u8bad\u7ec3\u8425', '\u535a\u5ba2', '\u603b\u7ed3', '\u6301\u7eed']

        breadth = self._make_indicator('learning_agility', 'breadth', '\u5b66\u4e60\u5e7f\u5ea6', 0.25, min(100.0, 35 + min(len(hard_skills), 8) * 6 + self._keyword_hits(evidences, breadth_keywords, tags=['resume', 'project', 'internship']) * 6), '35 + hard_skill_count*6 + breadth_hits*6', {'hard_skill_count': len(hard_skills)}, self._find_evidence_refs(evidences, keywords=hard_skills[:4] + breadth_keywords, tags=['resume', 'project', 'internship', 'manual_skill']))
        speed = self._make_indicator('learning_agility', 'speed', '\u5b66\u4e60\u901f\u5ea6', 0.25, min(100.0, 38 + self._keyword_hits(evidences, speed_keywords, tags=['resume', 'self_description', 'follow_up']) * 12), '38 + speed_hits*12', {'keywords': speed_keywords}, self._find_evidence_refs(evidences, keywords=speed_keywords, tags=['resume', 'self_description', 'follow_up']))
        transfer = self._make_indicator('learning_agility', 'transfer', '\u5b9e\u8df5\u8f6c\u5316', 0.30, min(100.0, 35 + self._keyword_hits(evidences, transfer_keywords, tags=['project', 'internship', 'resume']) * 12 + self._quantified_hits(evidences, tags=['project', 'internship']) * 8), '35 + transfer_hits*12 + quantified_hits*8', {'project_count': len(intake.project_experiences)}, self._find_evidence_refs(evidences, keywords=transfer_keywords, tags=['project', 'internship', 'resume']))
        growth = self._make_indicator('learning_agility', 'growth', '\u6301\u7eed\u6210\u957f', 0.20, min(100.0, 34 + len(intake.certificates) * 14 + self._keyword_hits(evidences, growth_keywords, tags=['certificate', 'resume', 'self_description']) * 10), '34 + certificate_count*14 + growth_hits*10', {'certificate_count': len(intake.certificates)}, self._find_evidence_refs(evidences, keywords=growth_keywords, tags=['certificate', 'resume', 'self_description']))
        return self._finalize_assessment(self._rule_by_code('learning_agility'), [breadth, speed, transfer, growth])

    def _score_execution(self, intake: StudentIntakeRequest, evidences: list[EvidenceItem]) -> SoftSkillAssessment:
        completion_keywords = ['\u5b8c\u6210', '\u5b9e\u73b0', '\u8d1f\u8d23', '\u4ea4\u4ed8', '\u4e0a\u7ebf', '\u5f00\u53d1']
        result_keywords = ['\u63d0\u5347', '\u51cf\u5c11', '\u4e0b\u964d', '\u589e\u957f', '\u4f18\u5316', '\u6548\u7387']
        cadence_keywords = ['\u6309\u65f6', '\u63a8\u8fdb', '\u8fed\u4ee3', '\u6bcf\u5468', '\u6301\u7eed', '\u8ddf\u8fdb']
        closure_keywords = ['\u95ed\u73af', '\u590d\u76d8', '\u8ddf\u8e2a', '\u4fee\u590d', '\u90e8\u7f72', '\u9a8c\u6536']

        completion = self._make_indicator('execution', 'completion', '\u4efb\u52a1\u5b8c\u6210', 0.30, min(100.0, 38 + self._keyword_hits(evidences, completion_keywords, tags=['project', 'internship', 'campus', 'resume']) * 11), '38 + completion_hits*11', {'keywords': completion_keywords}, self._find_evidence_refs(evidences, keywords=completion_keywords, tags=['project', 'internship', 'campus', 'resume']))
        quantified_hits = self._quantified_hits(evidences, tags=['project', 'internship', 'resume'])
        output = self._make_indicator('execution', 'output', '\u7ed3\u679c\u4ea7\u51fa', 0.30, min(100.0, 35 + quantified_hits * 18 + self._keyword_hits(evidences, result_keywords, tags=['project', 'internship', 'resume']) * 8), '35 + quantified_hits*18 + result_hits*8', {'quantified_hits': quantified_hits}, self._find_quantified_refs(evidences, tags=['project', 'internship', 'resume']))
        cadence = self._make_indicator('execution', 'cadence', '\u63a8\u8fdb\u8282\u594f', 0.20, min(100.0, 30 + len(intake.project_experiences) * 10 + len(intake.internship_experiences) * 14 + self._keyword_hits(evidences, cadence_keywords, tags=['project', 'internship', 'follow_up']) * 8), '30 + project_count*10 + internship_count*14 + cadence_hits*8', {'project_count': len(intake.project_experiences), 'internship_count': len(intake.internship_experiences)}, self._find_evidence_refs(evidences, keywords=cadence_keywords, tags=['project', 'internship', 'follow_up']))
        closure = self._make_indicator('execution', 'closure', '\u95ed\u73af\u610f\u8bc6', 0.20, min(100.0, 32 + self._keyword_hits(evidences, closure_keywords, tags=['project', 'internship', 'resume']) * 14), '32 + closure_hits*14', {'keywords': closure_keywords}, self._find_evidence_refs(evidences, keywords=closure_keywords, tags=['project', 'internship', 'resume']))
        return self._finalize_assessment(self._rule_by_code('execution'), [completion, output, cadence, closure])

    def _finalize_assessment(self, rule: SoftSkillRule, indicators: list[IndicatorScore]) -> SoftSkillAssessment:
        score = round(sum(item.weighted_score for item in indicators), 1)
        evidence_refs = self._unique([evidence_id for item in indicators for evidence_id in item.evidence_refs])
        level = self._score_level(score)
        strengths = [item.indicator_name for item in indicators if item.score >= 75]
        gaps = [item.indicator_name for item in indicators if item.score < 65]
        strength_text = '\u3001'.join(strengths[:2]) or '\u57fa\u7840\u8868\u73b0\u7a33\u5b9a'
        summary = f'{rule.skill_name}\u8bc4\u5206\u4e3a {score}\uff0c\u5f53\u524d\u8f83\u5f3a\u7684\u65b9\u9762\uff1a{strength_text}\u3002'
        if gaps:
            gap_text = '\u3001'.join(gaps[:2])
            summary += f' \u4ecd\u5efa\u8bae\u4f18\u5148\u8865\u5f3a\uff1a{gap_text}\u3002'
        suggestions = list(rule.suggestions[:2])
        if not gaps:
            suggestions = ['\u7ee7\u7eed\u6c89\u6dc0\u53ef\u91cf\u5316\u6210\u679c\uff0c\u4fdd\u6301\u4f18\u52bf\u8bc1\u636e\u66f4\u65b0', '\u5c06\u9ad8\u8d28\u91cf\u6848\u4f8b\u5199\u6210\u53ef\u590d\u7528\u7684\u7b80\u5386\u8868\u8fbe']
        return SoftSkillAssessment(
            skill_code=rule.skill_code,
            skill_name=rule.skill_name,
            score=score,
            level=level,
            summary=summary,
            evidence_refs=evidence_refs,
            indicators=indicators,
            suggestions=suggestions,
        )

    @staticmethod
    def _score_level(score: float) -> str:
        if score >= 85:
            return 'strong'
        if score >= 70:
            return 'solid'
        if score >= 55:
            return 'developing'
        return 'emerging'

    @staticmethod
    def _make_indicator(
        skill_code: str,
        code: str,
        name: str,
        weight: float,
        score: float,
        formula: str,
        raw_value: object,
        evidence_refs: list[str],
        deductions: Optional[list[ScoreDeduction]] = None,
    ) -> IndicatorScore:
        normalized = round(max(0.0, min(float(score), 100.0)), 1)
        return IndicatorScore(
            indicator_code=f'soft.{skill_code}.{code}',
            indicator_name=name,
            weight_in_dimension=weight,
            raw_value=raw_value,
            score=normalized,
            weighted_score=round(normalized * weight, 2),
            rule_id=f'soft.{skill_code}.{code}.v1',
            formula=formula,
            evidence_refs=evidence_refs,
            deductions=deductions or [],
            strengths=[f'{name}\u8bc1\u636e\u8f83\u5145\u5206'] if normalized >= 78 else [],
            gaps=[f'{name}\u8bc1\u636e\u4ecd\u53ef\u7ee7\u7eed\u8865\u5f3a'] if normalized < 65 else [],
        )

    def _keyword_hits(self, evidences: list[EvidenceItem], keywords: list[str], tags: Optional[list[str]] = None) -> int:
        matched: set[str] = set()
        tag_set = set(tags or [])
        for item in evidences:
            if tag_set and not (set(item.tags) & tag_set):
                continue
            haystack = f'{item.excerpt} {item.normalized_value}'.lower()
            for keyword in keywords:
                normalized = keyword.lower()
                if normalized in haystack:
                    matched.add(normalized)
        return len(matched)

    def _pattern_hits(self, evidences: list[EvidenceItem], patterns: list[str], tags: Optional[list[str]] = None) -> int:
        tag_set = set(tags or [])
        hit_count = 0
        for item in evidences:
            if tag_set and not (set(item.tags) & tag_set):
                continue
            haystack = f'{item.excerpt} {item.normalized_value}'
            if any(re.search(pattern, haystack, flags=re.IGNORECASE) for pattern in patterns):
                hit_count += 1
        return hit_count

    def _quantified_hits(self, evidences: list[EvidenceItem], tags: Optional[list[str]] = None) -> int:
        tag_set = set(tags or [])
        hit_count = 0
        for item in evidences:
            if tag_set and not (set(item.tags) & tag_set):
                continue
            haystack = f'{item.excerpt} {item.normalized_value}'
            if self.QUANTIFIED_PATTERN.search(haystack):
                hit_count += 1
        return hit_count

    def _find_quantified_refs(self, evidences: list[EvidenceItem], tags: Optional[list[str]] = None, limit: int = 5) -> list[str]:
        tag_set = set(tags or [])
        result: list[str] = []
        for item in evidences:
            if tag_set and not (set(item.tags) & tag_set):
                continue
            haystack = f'{item.excerpt} {item.normalized_value}'
            if self.QUANTIFIED_PATTERN.search(haystack):
                result.append(item.evidence_id)
            if len(result) >= limit:
                break
        return result

    def _find_evidence_refs(
        self,
        evidences: list[EvidenceItem],
        keywords: Optional[Iterable[str]] = None,
        tags: Optional[list[str]] = None,
        limit: int = 5,
    ) -> list[str]:
        normalized_keywords = [str(item).lower() for item in (keywords or []) if str(item).strip()]
        tag_set = set(tags or [])
        result: list[str] = []
        for item in evidences:
            if tag_set and not (set(item.tags) & tag_set):
                continue
            haystack = f'{item.excerpt} {item.normalized_value}'.lower()
            if not normalized_keywords or any(keyword in haystack for keyword in normalized_keywords):
                result.append(item.evidence_id)
            if len(result) >= limit:
                break
        return result

    def _rule_by_code(self, skill_code: str) -> SoftSkillRule:
        for rule in self.RULES:
            if rule.skill_code == skill_code:
                return rule
        raise KeyError(skill_code)

    @staticmethod
    def _unique(items: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for item in items:
            text = str(item).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
        return result
