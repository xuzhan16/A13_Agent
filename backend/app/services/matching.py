from datetime import datetime
from typing import Optional

from backend.app.schemas.common import DimensionScore, EvidenceItem, IndicatorScore, ScoreDeduction
from backend.app.schemas.job import (
    FinalScoreTrace,
    JobRequirementProfile,
    MatchEvidenceTrace,
    MatchResult,
    TraceVersionInfo,
)
from backend.app.schemas.student import StudentProfile


class MatchingService:
    BASE_WEIGHT = 0.15
    SKILL_WEIGHT = 0.45
    LITERACY_WEIGHT = 0.20
    POTENTIAL_WEIGHT = 0.20

    SCORE_RULE_VERSION = 'evidence-match/v1.0'
    EXTRACTOR_VERSION = 'student-profile/v2.0'

    DEGREE_SCORES = {
        '博士': 100,
        '硕士': 100,
        '研究生': 100,
        '本科': 100,
        '专科': 70,
        '大专': 70,
    }

    def rank_jobs(
        self,
        student_profile: StudentProfile,
        candidate_jobs: list[JobRequirementProfile],
    ) -> list[MatchResult]:
        results = [self._score_job(student_profile, job) for job in candidate_jobs]
        return sorted(results, key=lambda item: item.overall_score, reverse=True)

    def _score_job(
        self,
        student_profile: StudentProfile,
        job: JobRequirementProfile,
    ) -> MatchResult:
        matched_skills = sorted(set(student_profile.hard_skills) & set(job.required_skills + job.bonus_skills))
        missing_skills = [skill for skill in job.required_skills if skill not in student_profile.hard_skills]

        evidences = self._build_trace_evidences(student_profile, job)
        evidence_map = {item.evidence_id: item for item in evidences}

        base_dimension = self._score_base_requirements(student_profile, job, evidences, evidence_map)
        skill_dimension = self._score_skills(student_profile, job, evidences, evidence_map, matched_skills, missing_skills)
        literacy_dimension = self._score_literacy(student_profile, job, evidences, evidence_map)
        potential_dimension = self._score_potential(student_profile, job, evidences, evidence_map)
        dimension_scores = [base_dimension, skill_dimension, literacy_dimension, potential_dimension]

        raw_score = round(sum(item.weighted_score for item in dimension_scores), 2)
        overall = round(raw_score, 1)
        summary = self._build_summary(job.job_family, overall, matched_skills, missing_skills)

        evidence_trace = MatchEvidenceTrace(
            trace_id=f'{job.job_family}-{student_profile.basic_info.name or "anonymous"}-{datetime.now().strftime("%Y%m%d%H%M%S")}',
            generated_at=datetime.now().isoformat(timespec='seconds'),
            versions=TraceVersionInfo(
                score_rule_version=self.SCORE_RULE_VERSION,
                extractor_version=self.EXTRACTOR_VERSION,
                knowledge_base_version=self._knowledge_base_version(job),
            ),
            input_snapshot=self._build_input_snapshot(student_profile, job),
            evidences=evidences,
            dimensions=dimension_scores,
            final_score=FinalScoreTrace(
                raw_score=raw_score,
                display_score=int(round(raw_score)),
                formula='基础要求×0.15 + 职业技能×0.45 + 职业素养×0.20 + 发展潜力×0.20',
            ),
        )

        return MatchResult(
            job_family=job.job_family,
            overall_score=overall,
            summary=summary,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            dimension_scores=dimension_scores,
            evidence_trace=evidence_trace,
        )

    def _score_base_requirements(
        self,
        student_profile: StudentProfile,
        job: JobRequirementProfile,
        evidences: list[EvidenceItem],
        evidence_map: dict[str, EvidenceItem],
    ) -> DimensionScore:
        degree = student_profile.basic_info.degree.strip()
        major = student_profile.basic_info.major.strip()
        target_roles = student_profile.preference.target_roles

        degree_score = 55.0
        degree_deductions: list[ScoreDeduction] = []
        for keyword, score in self.DEGREE_SCORES.items():
            if keyword in degree:
                degree_score = float(score)
                break
        if not degree:
            degree_deductions.append(ScoreDeduction(reason='未提供学历信息，按保守规则计分', delta=-45))
        elif degree_score < 100:
            degree_deductions.append(ScoreDeduction(reason=f'当前学历为“{degree}”，未达到本科及以上满分档', delta=degree_score - 100))
        degree_indicator = self._build_indicator(
            indicator_code='basic.degree_alignment',
            indicator_name='学历匹配',
            weight_in_dimension=0.25,
            raw_value=degree or '未填写',
            score=degree_score,
            rule_id='basic.degree.v1',
            formula='博士/硕士/本科=100，专科/大专=70，缺失=55',
            evidence_refs=self._find_evidence_refs(evidences, tags=['degree']),
            deductions=degree_deductions,
            strengths=['学历达到岗位基础门槛'] if degree_score >= 100 else [],
            gaps=['建议补充学历证明信息'] if not degree else [],
        )

        major_score = self._score_major_alignment(major, job.preferred_majors)
        major_deductions: list[ScoreDeduction] = []
        if major_score < 100:
            major_deductions.append(ScoreDeduction(reason='专业与岗位推荐专业未完全重合', delta=major_score - 100))
        major_indicator = self._build_indicator(
            indicator_code='basic.major_alignment',
            indicator_name='专业匹配',
            weight_in_dimension=0.25,
            raw_value={'student_major': major or '未填写', 'preferred_majors': job.preferred_majors},
            score=major_score,
            rule_id='basic.major.v1',
            formula='推荐专业精确匹配=100，相关计算机大类=80，其他专业=45',
            evidence_refs=self._find_evidence_refs(evidences, tags=['major', 'job_preferred_majors']),
            deductions=major_deductions,
            strengths=['专业背景与岗位方向吻合'] if major_score >= 80 else [],
            gaps=['专业相关性一般，需用项目补强'] if major_score < 80 else [],
        )

        target_score = self._score_target_alignment(target_roles, job)
        target_indicator = self._build_indicator(
            indicator_code='basic.target_alignment',
            indicator_name='目标一致性',
            weight_in_dimension=0.20,
            raw_value=target_roles,
            score=target_score,
            rule_id='basic.target.v1',
            formula='目标岗位命中岗位族/别名=100，方向相近=85，未明确目标=50',
            evidence_refs=self._find_evidence_refs(evidences, tags=['target_role', 'job_profile']),
            deductions=[ScoreDeduction(reason='岗位目标不够聚焦', delta=target_score - 100)] if target_score < 100 else [],
            strengths=['目标岗位方向明确'] if target_score >= 85 else [],
            gaps=['建议明确主路径岗位名称'] if target_score < 85 else [],
        )

        practice_score = self._score_practice_readiness(student_profile)
        practice_deductions: list[ScoreDeduction] = []
        if student_profile.internship_count == 0:
            practice_deductions.append(ScoreDeduction(reason='暂无实习证据，基础门槛按项目经历折算', delta=-15))
        if student_profile.project_count == 0:
            practice_deductions.append(ScoreDeduction(reason='缺少项目经历，岗位基础支撑不足', delta=-30))
        practice_indicator = self._build_indicator(
            indicator_code='basic.practice_readiness',
            indicator_name='实践门槛',
            weight_in_dimension=0.30,
            raw_value={'project_count': student_profile.project_count, 'internship_count': student_profile.internship_count},
            score=practice_score,
            rule_id='basic.practice.v1',
            formula='有实习=100，2个及以上项目=85，1个项目=70，无项目=40',
            evidence_refs=self._find_evidence_refs(evidences, tags=['project', 'internship']),
            deductions=practice_deductions,
            strengths=['已有实践经历支撑岗位基础要求'] if practice_score >= 85 else [],
            gaps=['建议增加实习或高质量项目证明'] if practice_score < 85 else [],
        )

        return self._assemble_dimension(
            name='基础要求',
            dimension_code='basic_requirement',
            weight=self.BASE_WEIGHT,
            indicators=[degree_indicator, major_indicator, target_indicator, practice_indicator],
            evidence_map=evidence_map,
        )

    def _score_skills(
        self,
        student_profile: StudentProfile,
        job: JobRequirementProfile,
        evidences: list[EvidenceItem],
        evidence_map: dict[str, EvidenceItem],
        matched_skills: list[str],
        missing_skills: list[str],
    ) -> DimensionScore:
        required = set(job.required_skills)
        bonus = set(job.bonus_skills)
        student_skills = set(student_profile.hard_skills)

        required_overlap = sorted(required & student_skills)
        required_score = 60.0 if not required else round(len(required_overlap) / len(required) * 100, 1)
        required_indicator = self._build_indicator(
            indicator_code='skill.core_coverage',
            indicator_name='核心技能覆盖',
            weight_in_dimension=0.55,
            raw_value={'required_skills': job.required_skills, 'matched_required_skills': required_overlap},
            score=required_score,
            rule_id='skill.core.v1',
            formula='核心技能命中率 × 100',
            evidence_refs=self._find_evidence_refs(evidences, keywords=required_overlap or job.required_skills[:3], tags=['resume', 'manual_skill', 'project', 'internship', 'job_required_skills']),
            deductions=[ScoreDeduction(reason=f'未命中核心技能：{item}', delta=-round(100 / max(len(required), 1), 1)) for item in missing_skills[:4]],
            strengths=[f'命中核心技能：{item}' for item in required_overlap[:4]],
            gaps=[f'待补核心技能：{item}' for item in missing_skills[:4]],
        )

        bonus_overlap = sorted(bonus & student_skills)
        bonus_score = 70.0 if not bonus else round(len(bonus_overlap) / len(bonus) * 100, 1)
        bonus_indicator = self._build_indicator(
            indicator_code='skill.bonus_coverage',
            indicator_name='加分技能覆盖',
            weight_in_dimension=0.15,
            raw_value={'bonus_skills': job.bonus_skills, 'matched_bonus_skills': bonus_overlap},
            score=bonus_score,
            rule_id='skill.bonus.v1',
            formula='加分技能命中率 × 100；若岗位未配置加分技能则给 70 分基线',
            evidence_refs=self._find_evidence_refs(evidences, keywords=bonus_overlap or job.bonus_skills[:2], tags=['resume', 'manual_skill', 'project', 'internship', 'job_bonus_skills']),
            deductions=[] if bonus_score >= 100 else [ScoreDeduction(reason='加分技能未完全覆盖', delta=bonus_score - 100)],
            strengths=[f'已具备加分技能：{item}' for item in bonus_overlap[:3]],
            gaps=[f'可补充加分技能：{item}' for item in sorted(bonus - student_skills)[:3]],
        )

        project_hits = self._keyword_hits(evidences, job.required_skills + job.bonus_skills, tags=['project', 'internship'])
        project_score = min(100.0, round(45 + student_profile.project_count * 14 + student_profile.internship_count * 10 + project_hits * 6, 1))
        project_indicator = self._build_indicator(
            indicator_code='skill.project_evidence',
            indicator_name='项目技能证据',
            weight_in_dimension=0.20,
            raw_value={'project_count': student_profile.project_count, 'internship_count': student_profile.internship_count, 'project_skill_hits': project_hits},
            score=project_score,
            rule_id='skill.project.v1',
            formula='45 + 项目数×14 + 实习数×10 + 项目内技能命中×6，上限 100',
            evidence_refs=self._find_evidence_refs(evidences, tags=['project', 'internship']),
            deductions=[ScoreDeduction(reason='缺少真实业务实习，项目证据主要来自校内经历', delta=-10)] if student_profile.internship_count == 0 else [],
            strengths=['项目描述中体现了技术栈与职责'] if project_score >= 80 else [],
            gaps=['建议增加量化成果、性能优化或真实业务复杂度'] if project_score < 80 else [],
        )

        engineering_keywords = ['git', 'github', 'maven', 'junit', 'linux', 'docker', '部署', '联调', 'review', '测试']
        engineering_hits = self._keyword_hits(evidences, engineering_keywords, tags=['resume', 'manual_skill', 'project', 'internship', 'campus'])
        engineering_score = min(100.0, round(40 + engineering_hits * 10, 1))
        engineering_indicator = self._build_indicator(
            indicator_code='skill.engineering_practice',
            indicator_name='工程化实践',
            weight_in_dimension=0.10,
            raw_value={'engineering_hits': engineering_hits, 'keywords': engineering_keywords},
            score=engineering_score,
            rule_id='skill.engineering.v1',
            formula='40 + 工程化关键词命中数×10，上限 100',
            evidence_refs=self._find_evidence_refs(evidences, keywords=engineering_keywords, tags=['resume', 'project', 'internship', 'campus']),
            deductions=[ScoreDeduction(reason='缺少 CI/CD、部署或测试覆盖等更强工程证据', delta=-15)] if engineering_score < 85 else [],
            strengths=['存在工程协作或测试实践证据'] if engineering_score >= 75 else [],
            gaps=['建议补充部署、测试、代码审查等工程化实践'] if engineering_score < 75 else [],
        )

        return self._assemble_dimension(
            name='职业技能',
            dimension_code='professional_skill',
            weight=self.SKILL_WEIGHT,
            indicators=[required_indicator, bonus_indicator, project_indicator, engineering_indicator],
            evidence_map=evidence_map,
        )

    def _score_literacy(
        self,
        student_profile: StudentProfile,
        job: JobRequirementProfile,
        evidences: list[EvidenceItem],
        evidence_map: dict[str, EvidenceItem],
    ) -> DimensionScore:
        required = set(job.soft_skills)
        actual = set(student_profile.soft_skills)
        overlap = sorted(required & actual)
        soft_score = 60.0 if not required else round(55 + len(overlap) / len(required) * 45, 1)
        soft_indicator = self._build_indicator(
            indicator_code='literacy.soft_skill_coverage',
            indicator_name='岗位素养覆盖',
            weight_in_dimension=0.35,
            raw_value={'required_soft_skills': job.soft_skills, 'matched_soft_skills': overlap},
            score=soft_score,
            rule_id='literacy.coverage.v1',
            formula='55 + 素养命中率×45；若岗位未配置素养词则给 60 分基线',
            evidence_refs=self._find_evidence_refs(evidences, keywords=overlap or job.soft_skills[:2], tags=['resume', 'self_description', 'campus', 'internship', 'job_soft_skills']),
            deductions=[ScoreDeduction(reason=f'缺少岗位素养证据：{item}', delta=-8) for item in sorted(required - actual)[:4]],
            strengths=[f'已体现素养：{item}' for item in overlap[:4]],
            gaps=[f'待补素养证明：{item}' for item in sorted(required - actual)[:4]],
        )

        teamwork_keywords = ['团队', '协作', '联调', '合作', '组织']
        teamwork_hits = self._keyword_hits(evidences, teamwork_keywords, tags=['project', 'internship', 'campus'])
        teamwork_score = min(100.0, round(45 + teamwork_hits * 12 + (10 if student_profile.campus_count >= 1 else 0), 1))
        teamwork_indicator = self._build_indicator(
            indicator_code='literacy.teamwork',
            indicator_name='团队协作',
            weight_in_dimension=0.20,
            raw_value={'teamwork_hits': teamwork_hits},
            score=teamwork_score,
            rule_id='literacy.teamwork.v1',
            formula='45 + 协作关键词命中×12 + 校园组织经历加分',
            evidence_refs=self._find_evidence_refs(evidences, keywords=teamwork_keywords, tags=['project', 'internship', 'campus']),
            deductions=[] if teamwork_score >= 75 else [ScoreDeduction(reason='协作分工证据偏少', delta=teamwork_score - 75)],
            strengths=['体现了协作、联调或组织能力'] if teamwork_score >= 75 else [],
            gaps=['建议补充协作分工、跨角色联动描述'] if teamwork_score < 75 else [],
        )

        ownership_keywords = ['负责', '主导', '推进', '跟进', '组长', 'review']
        ownership_hits = self._keyword_hits(evidences, ownership_keywords, tags=['project', 'internship', 'campus'])
        ownership_score = min(100.0, round(40 + ownership_hits * 12, 1))
        ownership_indicator = self._build_indicator(
            indicator_code='literacy.ownership',
            indicator_name='责任意识',
            weight_in_dimension=0.20,
            raw_value={'ownership_hits': ownership_hits},
            score=ownership_score,
            rule_id='literacy.ownership.v1',
            formula='40 + 负责/主导类关键词命中×12，上限 100',
            evidence_refs=self._find_evidence_refs(evidences, keywords=ownership_keywords, tags=['project', 'internship', 'campus']),
            deductions=[] if ownership_score >= 70 else [ScoreDeduction(reason='主导或负责证据较少', delta=ownership_score - 70)],
            strengths=['存在负责模块或组织推进证据'] if ownership_score >= 70 else [],
            gaps=['建议明确个人负责范围和交付结果'] if ownership_score < 70 else [],
        )

        problem_keywords = ['优化', '排查', '定位', '分析', '解决', '改进', '下降', '提升']
        problem_hits = self._keyword_hits(evidences, problem_keywords, tags=['resume', 'project', 'internship'])
        problem_score = min(100.0, round(45 + problem_hits * 10, 1))
        problem_indicator = self._build_indicator(
            indicator_code='literacy.problem_solving',
            indicator_name='问题分析',
            weight_in_dimension=0.15,
            raw_value={'problem_hits': problem_hits},
            score=problem_score,
            rule_id='literacy.problem.v1',
            formula='45 + 优化/排查类关键词命中×10，上限 100',
            evidence_refs=self._find_evidence_refs(evidences, keywords=problem_keywords, tags=['resume', 'project', 'internship']),
            deductions=[] if problem_score >= 75 else [ScoreDeduction(reason='缺少问题定位或优化结果证据', delta=problem_score - 75)],
            strengths=['有优化或问题排查证据'] if problem_score >= 75 else [],
            gaps=['建议补充量化结果和问题解决过程'] if problem_score < 75 else [],
        )

        expression_keywords = ['汇报', '分享', '沟通', '文档', '答辩', '说明']
        expression_hits = self._keyword_hits(evidences, expression_keywords, tags=['self_description', 'campus', 'follow_up'])
        expression_score = min(100.0, round(40 + expression_hits * 12, 1))
        expression_indicator = self._build_indicator(
            indicator_code='literacy.expression',
            indicator_name='表达沟通',
            weight_in_dimension=0.10,
            raw_value={'expression_hits': expression_hits},
            score=expression_score,
            rule_id='literacy.expression.v1',
            formula='40 + 沟通/汇报类关键词命中×12，上限 100',
            evidence_refs=self._find_evidence_refs(evidences, keywords=expression_keywords, tags=['self_description', 'campus', 'follow_up']),
            deductions=[] if expression_score >= 70 else [ScoreDeduction(reason='表达汇报证据较弱', delta=expression_score - 70)],
            strengths=['有表达或汇报证据'] if expression_score >= 70 else [],
            gaps=['建议补充汇报、答辩或文档协作经验'] if expression_score < 70 else [],
        )

        return self._assemble_dimension(
            name='职业素养',
            dimension_code='professional_literacy',
            weight=self.LITERACY_WEIGHT,
            indicators=[soft_indicator, teamwork_indicator, ownership_indicator, problem_indicator, expression_indicator],
            evidence_map=evidence_map,
        )

    def _score_potential(
        self,
        student_profile: StudentProfile,
        job: JobRequirementProfile,
        evidences: list[EvidenceItem],
        evidence_map: dict[str, EvidenceItem],
    ) -> DimensionScore:
        learning_keywords = ['学习', '自学', '笔记', '课程', '刷题', '总结', '优化', '研究']
        learning_hits = self._keyword_hits(evidences, learning_keywords, tags=['resume', 'self_description', 'project', 'follow_up'])
        learning_score = min(100.0, round(50 + learning_hits * 8 + (10 if '学习能力' in student_profile.soft_skills else 0), 1))
        learning_indicator = self._build_indicator(
            indicator_code='potential.learning_agility',
            indicator_name='学习敏捷度',
            weight_in_dimension=0.35,
            raw_value={'learning_hits': learning_hits, 'soft_skills': student_profile.soft_skills},
            score=learning_score,
            rule_id='potential.learning.v1',
            formula='50 + 学习类关键词命中×8 + 学习能力标签加分，上限 100',
            evidence_refs=self._find_evidence_refs(evidences, keywords=learning_keywords, tags=['resume', 'self_description', 'follow_up', 'project']),
            deductions=[] if learning_score >= 80 else [ScoreDeduction(reason='缺少自学、复盘或持续成长证据', delta=learning_score - 80)],
            strengths=['有持续学习与自我提升迹象'] if learning_score >= 80 else [],
            gaps=['建议补充刷题、技术笔记或学习路径'] if learning_score < 80 else [],
        )

        growth_score = min(100.0, round(40 + student_profile.project_count * 16 + student_profile.internship_count * 18 + student_profile.campus_count * 8, 1))
        growth_indicator = self._build_indicator(
            indicator_code='potential.growth_curve',
            indicator_name='成长曲线',
            weight_in_dimension=0.30,
            raw_value={'project_count': student_profile.project_count, 'internship_count': student_profile.internship_count, 'campus_count': student_profile.campus_count},
            score=growth_score,
            rule_id='potential.growth.v1',
            formula='40 + 项目数×16 + 实习数×18 + 校园经历数×8，上限 100',
            evidence_refs=self._find_evidence_refs(evidences, tags=['project', 'internship', 'campus']),
            deductions=[] if growth_score >= 80 else [ScoreDeduction(reason='成长路径证据仍偏早期', delta=growth_score - 80)],
            strengths=['经历结构较完整，具备持续成长基础'] if growth_score >= 80 else [],
            gaps=['建议增加更高难度项目或真实业务经历'] if growth_score < 80 else [],
        )

        goal_score = min(100.0, round(35 + (25 if student_profile.preference.target_roles else 0) + (15 if student_profile.preference.target_cities else 0) + (15 if any(item.source_type == 'follow_up_answer' for item in evidences) else 0) + (10 if any(item.source_type == 'self_description' for item in evidences) else 0), 1))
        goal_indicator = self._build_indicator(
            indicator_code='potential.goal_clarity',
            indicator_name='目标清晰度',
            weight_in_dimension=0.20,
            raw_value={'target_roles': student_profile.preference.target_roles, 'target_cities': student_profile.preference.target_cities},
            score=goal_score,
            rule_id='potential.goal.v1',
            formula='35 + 目标岗位/城市/追问/自述证据累加，上限 100',
            evidence_refs=self._find_evidence_refs(evidences, tags=['target_role', 'target_city', 'follow_up', 'self_description']),
            deductions=[] if goal_score >= 85 else [ScoreDeduction(reason='职业目标仍可进一步聚焦', delta=goal_score - 85)],
            strengths=['求职目标较清晰'] if goal_score >= 85 else [],
            gaps=['建议进一步明确主岗与备选岗'] if goal_score < 85 else [],
        )

        credential_score = min(100.0, round(45 + len(student_profile.certificates) * 18, 1))
        credential_indicator = self._build_indicator(
            indicator_code='potential.credential_support',
            indicator_name='标准化证明',
            weight_in_dimension=0.15,
            raw_value={'certificates': student_profile.certificates},
            score=credential_score,
            rule_id='potential.credential.v1',
            formula='45 + 证书数量×18，上限 100',
            evidence_refs=self._find_evidence_refs(evidences, tags=['certificate']),
            deductions=[] if student_profile.certificates else [ScoreDeduction(reason='暂无证书或标准化证明材料', delta=-20)],
            strengths=['有证书或标准化证明材料'] if student_profile.certificates else [],
            gaps=['可补充证书、竞赛或课程认证'] if not student_profile.certificates else [],
        )

        return self._assemble_dimension(
            name='发展潜力',
            dimension_code='development_potential',
            weight=self.POTENTIAL_WEIGHT,
            indicators=[learning_indicator, growth_indicator, goal_indicator, credential_indicator],
            evidence_map=evidence_map,
        )

    @staticmethod
    def _build_indicator(
        indicator_code: str,
        indicator_name: str,
        weight_in_dimension: float,
        raw_value: object,
        score: float,
        rule_id: str,
        formula: str,
        evidence_refs: list[str],
        deductions: Optional[list[ScoreDeduction]] = None,
        strengths: Optional[list[str]] = None,
        gaps: Optional[list[str]] = None,
    ) -> IndicatorScore:
        normalized_score = round(max(min(score, 100), 0), 1)
        return IndicatorScore(
            indicator_code=indicator_code,
            indicator_name=indicator_name,
            weight_in_dimension=weight_in_dimension,
            raw_value=raw_value,
            score=normalized_score,
            weighted_score=round(normalized_score * weight_in_dimension, 2),
            rule_id=rule_id,
            formula=formula,
            evidence_refs=evidence_refs,
            deductions=deductions or [],
            strengths=strengths or [],
            gaps=gaps or [],
        )

    def _assemble_dimension(
        self,
        name: str,
        dimension_code: str,
        weight: float,
        indicators: list[IndicatorScore],
        evidence_map: dict[str, EvidenceItem],
    ) -> DimensionScore:
        dimension_score = round(sum(item.weighted_score for item in indicators), 1)
        evidence_refs: list[str] = []
        for indicator in indicators:
            for evidence_id in indicator.evidence_refs:
                if evidence_id not in evidence_refs:
                    evidence_refs.append(evidence_id)
        strengths: list[str] = []
        gaps: list[str] = []
        for indicator in indicators:
            strengths.extend(indicator.strengths)
            gaps.extend(indicator.gaps)
        return DimensionScore(
            name=name,
            dimension_code=dimension_code,
            score=dimension_score,
            weight=weight,
            weighted_score=round(dimension_score * weight, 2),
            formula=' + '.join(f'{item.indicator_name}×{item.weight_in_dimension}' for item in indicators),
            strengths=self._unique_text(strengths),
            gaps=self._unique_text(gaps),
            evidences=[evidence_map[item] for item in evidence_refs if item in evidence_map],
            indicators=indicators,
        )

    def _build_trace_evidences(
        self,
        student_profile: StudentProfile,
        job: JobRequirementProfile,
    ) -> list[EvidenceItem]:
        evidences: list[EvidenceItem] = []
        for index, item in enumerate(student_profile.evidences, start=1):
            payload = item.dict() if hasattr(item, 'dict') else {'source': getattr(item, 'source', 'student_profile'), 'excerpt': getattr(item, 'excerpt', '')}
            evidences.append(
                EvidenceItem(
                    evidence_id=payload.get('evidence_id') or f'S{index:02d}',
                    source=payload.get('source', 'student_profile'),
                    source_type=payload.get('source_type') or payload.get('source', 'student_profile'),
                    source_ref=payload.get('source_ref') or f'student_profile.evidences[{index - 1}]',
                    excerpt=payload.get('excerpt', ''),
                    normalized_value=payload.get('normalized_value', ''),
                    confidence=float(payload.get('confidence', 1.0)),
                    extract_rule=payload.get('extract_rule', 'carry_over'),
                    tags=list(payload.get('tags', [])),
                )
            )

        evidences.extend([
            self._make_evidence('J01', 'job_profile', 'job_knowledge_base', f'job_profile.{job.job_family}.description', job.description or f'{job.job_family} 岗位画像', job.job_family, 'knowledge_base_profile', ['job_profile']),
            self._make_evidence('J02', 'job_profile', 'job_knowledge_base', f'job_profile.{job.job_family}.preferred_majors', f'岗位推荐专业：{"、".join(job.preferred_majors) or "未配置"}', job.preferred_majors, 'knowledge_base_profile', ['job_preferred_majors']),
            self._make_evidence('J03', 'job_profile', 'job_knowledge_base', f'job_profile.{job.job_family}.required_skills', f'岗位核心技能：{"、".join(job.required_skills) or "未配置"}', job.required_skills, 'knowledge_base_profile', ['job_required_skills']),
            self._make_evidence('J04', 'job_profile', 'job_knowledge_base', f'job_profile.{job.job_family}.bonus_skills', f'岗位加分技能：{"、".join(job.bonus_skills) or "未配置"}', job.bonus_skills, 'knowledge_base_profile', ['job_bonus_skills']),
            self._make_evidence('J05', 'job_profile', 'job_knowledge_base', f'job_profile.{job.job_family}.soft_skills', f'岗位素养要求：{"、".join(job.soft_skills) or "未配置"}', job.soft_skills, 'knowledge_base_profile', ['job_soft_skills']),
        ])
        return evidences

    @staticmethod
    def _make_evidence(
        evidence_id: str,
        source: str,
        source_type: str,
        source_ref: str,
        excerpt: str,
        normalized_value: object,
        extract_rule: str,
        tags: list[str],
    ) -> EvidenceItem:
        return EvidenceItem(
            evidence_id=evidence_id,
            source=source,
            source_type=source_type,
            source_ref=source_ref,
            excerpt=excerpt,
            normalized_value=normalized_value,
            confidence=1.0,
            extract_rule=extract_rule,
            tags=tags,
        )

    @staticmethod
    def _score_major_alignment(major: str, preferred_majors: list[str]) -> float:
        major_text = major.lower()
        if any(keyword.lower() in major_text for keyword in preferred_majors):
            return 100.0
        broad_related = ['计算机', '软件', '信息', '网络', '电子', '通信', '自动化']
        if any(keyword in major_text for keyword in broad_related):
            return 80.0
        if major_text:
            return 45.0
        return 40.0

    @staticmethod
    def _score_target_alignment(target_roles: list[str], job: JobRequirementProfile) -> float:
        if not target_roles:
            return 50.0
        target_text = ' '.join(target_roles).lower()
        aliases = [job.job_family.lower(), *[item.lower() for item in job.aliases]]
        if any(item and item in target_text for item in aliases):
            return 100.0
        if ('开发' in target_text and '开发' in job.job_family) or ('后端' in target_text and 'java' in job.job_family.lower()):
            return 85.0
        return 60.0

    @staticmethod
    def _score_practice_readiness(student_profile: StudentProfile) -> float:
        if student_profile.internship_count >= 1:
            return 100.0
        if student_profile.project_count >= 2:
            return 85.0
        if student_profile.project_count == 1:
            return 70.0
        return 40.0

    @staticmethod
    def _find_evidence_refs(
        evidences: list[EvidenceItem],
        keywords: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        limit: int = 6,
    ) -> list[str]:
        keywords = [item.lower() for item in (keywords or []) if str(item).strip()]
        tag_set = set(tags or [])
        matched: list[str] = []
        for item in evidences:
            haystack = f'{item.excerpt} {item.normalized_value}'.lower()
            item_tags = set(item.tags)
            keyword_hit = not keywords or any(keyword in haystack for keyword in keywords)
            tag_hit = not tag_set or bool(item_tags & tag_set)
            if keyword_hit and tag_hit:
                matched.append(item.evidence_id)
            if len(matched) >= limit:
                break
        return matched

    @staticmethod
    def _keyword_hits(
        evidences: list[EvidenceItem],
        keywords: list[str],
        tags: Optional[list[str]] = None,
    ) -> int:
        tag_set = set(tags or [])
        hits: set[str] = set()
        for item in evidences:
            if tag_set and not (set(item.tags) & tag_set):
                continue
            haystack = f'{item.excerpt} {item.normalized_value}'.lower()
            for keyword in keywords:
                normalized = str(keyword).strip().lower()
                if normalized and normalized in haystack:
                    hits.add(normalized)
        return len(hits)

    @staticmethod
    def _build_input_snapshot(
        student_profile: StudentProfile,
        job: JobRequirementProfile,
    ) -> dict[str, object]:
        return {
            'student_profile': {
                'name': student_profile.basic_info.name,
                'major': student_profile.basic_info.major,
                'degree': student_profile.basic_info.degree,
                'target_roles': student_profile.preference.target_roles,
                'target_cities': student_profile.preference.target_cities,
                'hard_skills': student_profile.hard_skills,
                'soft_skills': student_profile.soft_skills,
                'project_count': student_profile.project_count,
                'internship_count': student_profile.internship_count,
                'campus_count': student_profile.campus_count,
                'certificates': student_profile.certificates,
            },
            'job_requirement': {
                'job_family': job.job_family,
                'preferred_majors': job.preferred_majors,
                'required_skills': job.required_skills,
                'bonus_skills': job.bonus_skills,
                'soft_skills': job.soft_skills,
                'practice_requirements': job.practice_requirements,
            },
        }

    @staticmethod
    def _knowledge_base_version(job: JobRequirementProfile) -> str:
        if job.sample_count > 0:
            return f'job-kb/samples-{job.sample_count}'
        return 'job-kb/static'

    @staticmethod
    def _unique_text(items: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for item in items:
            text = str(item).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
        return result

    @staticmethod
    def _build_summary(
        job_family: str,
        overall_score: float,
        matched_skills: list[str],
        missing_skills: list[str],
    ) -> str:
        strengths = '、'.join(matched_skills[:3]) if matched_skills else '暂无明显命中技能'
        gap = '、'.join(missing_skills[:3]) if missing_skills else '核心技能覆盖较完整'
        return (
            f'当前与“{job_family}”的综合匹配度为 {overall_score} 分。'
            f'主要优势集中在：{strengths}；'
            f'当前优先补齐方向：{gap}。'
        )
