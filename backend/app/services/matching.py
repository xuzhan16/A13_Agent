from backend.app.schemas.common import DimensionScore, EvidenceItem
from backend.app.schemas.job import JobRequirementProfile, MatchResult
from backend.app.schemas.student import StudentProfile


class MatchingService:
    BASE_WEIGHT = 0.15
    SKILL_WEIGHT = 0.45
    LITERACY_WEIGHT = 0.20
    POTENTIAL_WEIGHT = 0.20

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
        base_dimension = self._score_base_requirements(student_profile, job)
        skill_dimension = self._score_skills(student_profile, job)
        literacy_dimension = self._score_literacy(student_profile, job)
        potential_dimension = self._score_potential(student_profile, job)

        overall = round(
            base_dimension.score * self.BASE_WEIGHT
            + skill_dimension.score * self.SKILL_WEIGHT
            + literacy_dimension.score * self.LITERACY_WEIGHT
            + potential_dimension.score * self.POTENTIAL_WEIGHT,
            1,
        )

        matched_skills = sorted(set(student_profile.hard_skills) & set(job.required_skills + job.bonus_skills))
        missing_skills = [skill for skill in job.required_skills if skill not in student_profile.hard_skills]
        summary = self._build_summary(job.job_family, overall, matched_skills, missing_skills)

        return MatchResult(
            job_family=job.job_family,
            overall_score=overall,
            summary=summary,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            dimension_scores=[
                base_dimension,
                skill_dimension,
                literacy_dimension,
                potential_dimension,
            ],
        )

    def _score_base_requirements(
        self,
        student_profile: StudentProfile,
        job: JobRequirementProfile,
    ) -> DimensionScore:
        major_text = student_profile.basic_info.major.lower()
        major_match = any(keyword.lower() in major_text for keyword in job.preferred_majors)
        practice_ready = student_profile.project_count + student_profile.internship_count > 0
        score = 55
        strengths: list[str] = []
        gaps: list[str] = []

        if major_match:
            score += 25
            strengths.append('专业背景与岗位方向较吻合')
        else:
            gaps.append('专业背景与目标岗位未形成明显强关联')

        if practice_ready:
            score += 15
            strengths.append('具备实践经历支撑岗位基础要求')
        else:
            gaps.append('缺少实践经历支撑基础要求')

        return DimensionScore(
            name='基础要求',
            score=min(score, 100),
            weight=self.BASE_WEIGHT,
            strengths=strengths,
            gaps=gaps,
            evidences=self._profile_evidences(student_profile),
        )

    def _score_skills(
        self,
        student_profile: StudentProfile,
        job: JobRequirementProfile,
    ) -> DimensionScore:
        required = set(job.required_skills)
        bonus = set(job.bonus_skills)
        student_skills = set(student_profile.hard_skills)

        required_overlap = len(required & student_skills)
        bonus_overlap = len(bonus & student_skills)

        required_score = 0 if not required else required_overlap / len(required) * 80
        bonus_score = 0 if not bonus else bonus_overlap / len(bonus) * 20
        score = round(required_score + bonus_score, 1)

        return DimensionScore(
            name='职业技能',
            score=score,
            weight=self.SKILL_WEIGHT,
            strengths=[f'已命中技能：{skill}' for skill in sorted(required & student_skills)],
            gaps=[f'待补技能：{skill}' for skill in sorted(required - student_skills)],
            evidences=self._profile_evidences(student_profile),
        )

    def _score_literacy(
        self,
        student_profile: StudentProfile,
        job: JobRequirementProfile,
    ) -> DimensionScore:
        required = set(job.soft_skills)
        actual = set(student_profile.soft_skills)
        overlap = len(required & actual)
        score = round(40 + (0 if not required else overlap / len(required) * 60), 1)

        return DimensionScore(
            name='职业素养',
            score=min(score, 100),
            weight=self.LITERACY_WEIGHT,
            strengths=[f'已体现素养：{skill}' for skill in sorted(required & actual)],
            gaps=[f'建议补充素养证明：{skill}' for skill in sorted(required - actual)],
            evidences=self._profile_evidences(student_profile),
        )

    def _score_potential(
        self,
        student_profile: StudentProfile,
        job: JobRequirementProfile,
    ) -> DimensionScore:
        score = 35
        strengths: list[str] = []
        gaps: list[str] = []

        if student_profile.project_count >= 1:
            score += 20
            strengths.append('具备项目实践，成长潜力较好')
        else:
            gaps.append('项目经历不足，潜力证明不够充分')

        if student_profile.internship_count >= 1:
            score += 25
            strengths.append('具备实习经历，岗位适应速度更快')
        else:
            gaps.append('缺少实习经历，职场适应性证据不足')

        if '学习能力' in student_profile.soft_skills:
            score += 10
            strengths.append('学习能力有明确证据')

        if student_profile.certificates:
            score += 10
            strengths.append('具备额外认证证明')
        else:
            gaps.append('可增加证书或标准化证明材料')

        return DimensionScore(
            name='发展潜力',
            score=min(score, 100),
            weight=self.POTENTIAL_WEIGHT,
            strengths=strengths,
            gaps=gaps,
            evidences=self._profile_evidences(student_profile),
        )

    @staticmethod
    def _profile_evidences(student_profile: StudentProfile) -> list[EvidenceItem]:
        return student_profile.evidences[:3]

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
