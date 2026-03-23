import re
from collections import defaultdict
from typing import Optional

from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.resume import (
    ResumeBasicInfo,
    ResumeCertificateItem,
    ResumeExperienceItem,
    ResumeExtractionField,
    ResumeFormFillSuggestion,
    ResumeInnovationIndicators,
    ResumePendingField,
    ResumeSkillItem,
    ResumeStructuredProfile,
    ResumeStructuredSkills,
)


class ResumeStructuringService:
    SECTION_ALIASES = {
        '教育经历': 'education',
        '教育背景': 'education',
        '教育': 'education',
        '项目经历': 'project',
        '项目经验': 'project',
        '项目': 'project',
        '实习经历': 'internship',
        '实习经验': 'internship',
        '工作经历': 'internship',
        '工作经验': 'internship',
        '校园经历': 'campus',
        '校园实践': 'campus',
        '学生工作': 'campus',
        '技能': 'skills',
        '专业技能': 'skills',
        '技能特长': 'skills',
        '证书': 'certificate',
        '证书资格': 'certificate',
        '荣誉奖项': 'award',
        '获奖经历': 'award',
        '获奖情况': 'award',
        '科研成果': 'innovation',
        '创新经历': 'innovation',
        '创业经历': 'innovation',
        '自我评价': 'self_description',
        '个人评价': 'self_description',
        '个人总结': 'self_description',
    }

    DEGREE_ORDER = ['博士', '硕士', '研究生', '本科', '专科', '大专']
    SCHOOL_PATTERN = re.compile(r'([A-Za-z0-9\u4e00-\u9fa5·()（）-]{2,40}(?:大学|学院|学校))')
    GRAD_YEAR_PATTERN = re.compile(r'(20\d{2})(?:届|年毕业|年)?')
    TIME_RANGE_PATTERN = re.compile(
        r'((?:20\d{2}[./年-]\d{1,2}(?:月)?)\s*(?:-|–|—|~|～|至)\s*(?:今|至今|现在|20\d{2}[./年-]\d{1,2}(?:月)?))'
    )
    PHONE_PATTERN = re.compile(r'1[3-9]\d{9}')
    EMAIL_PATTERN = re.compile(r'[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+')
    PROJECT_TITLE_HINTS = ('项目', '系统', '平台', '小程序', '网站', 'App', 'APP', '程序')
    DETAIL_PREFIXES = ('项目描述', '描述', '职责', '负责', '主要负责', '工作内容', '技术栈', '使用', '成果', '亮点', '角色')
    CERTIFICATE_HINTS = ('证书', '资格', '四级', '六级', '软考', 'PMP', '计算机二级', '教师资格', '证券从业', 'HCIA', 'HCIP')
    AWARD_HINTS = ('一等奖', '二等奖', '三等奖', '优秀', '冠军', '亚军', '季军', '获奖', '荣誉')
    PATENT_HINTS = ('专利', '发明专利', '实用新型')
    PUBLICATION_HINTS = ('论文', '发表', '期刊', '会议', 'SCI', 'EI', '北大核心')
    ENTREPRENEURSHIP_HINTS = ('创业', '创始人', '联合创始人', '孵化', '营收', '商业计划')

    SKILL_ALIASES = {
        'springboot': 'Spring Boot',
        'spring boot': 'Spring Boot',
        'springcloud': 'Spring Cloud',
        'spring cloud': 'Spring Cloud',
        'mybatis': 'MyBatis',
        'mysql': 'MySQL',
        'redis': 'Redis',
        'postgresql': 'PostgreSQL',
        'postgres': 'PostgreSQL',
        'sqlserver': 'SQL Server',
        'sql server': 'SQL Server',
        'oracle': 'Oracle',
        'vue.js': 'Vue',
        'vue': 'Vue',
        'react.js': 'React',
        'react': 'React',
        'javascript': 'JavaScript',
        'typescript': 'TypeScript',
        'node.js': 'Node.js',
        'nodejs': 'Node.js',
        'golang': 'Go',
        'c++': 'C++',
        'c#': 'C#',
        'python': 'Python',
        'java': 'Java',
        'gitlab': 'Git',
        'github': 'Git',
        'git': 'Git',
        'docker': 'Docker',
        'linux': 'Linux',
        'maven': 'Maven',
        'gradle': 'Gradle',
        'junit': 'JUnit',
        'pytest': 'PyTest',
        'fastapi': 'FastAPI',
        'django': 'Django',
        'flask': 'Flask',
        'kafka': 'Kafka',
        'rabbitmq': 'RabbitMQ',
        'elasticsearch': 'Elasticsearch',
        'k8s': 'Kubernetes',
        'kubernetes': 'Kubernetes',
    }

    LANGUAGE_SKILLS = {'Java', 'Python', 'C', 'C++', 'C#', 'Go', 'JavaScript', 'TypeScript', 'PHP', 'Ruby', 'Rust', 'Kotlin', 'Scala', 'SQL'}
    FRAMEWORK_SKILLS = {'Spring Boot', 'Spring Cloud', 'MyBatis', 'Django', 'Flask', 'FastAPI', 'Vue', 'React', 'Angular', 'Node.js'}

    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository
        self.skill_lexicon = repository.get_skill_lexicon()
        self.skill_alias_map = self._build_skill_alias_map(self.skill_lexicon)

    def structure(self, text: str, file_name: str = '') -> ResumeStructuredProfile:
        normalized_text = self._normalize_text(text)
        lines = self._split_lines(normalized_text)
        sections = self._split_sections(lines)

        basic_info = self._extract_basic_info(lines, sections)
        skills = self._extract_skills(lines, sections)
        projects = self._extract_projects(sections, skills)
        internships = self._extract_internships(sections, skills)
        campus = self._extract_campus_experiences(sections, skills)
        certificates = self._extract_certificates(lines, sections)
        innovation = self._extract_innovation(lines, sections)
        pending_fields = self._collect_pending_fields(basic_info, projects, internships, campus, certificates)
        notes = self._build_notes(file_name, sections, projects, internships, campus)
        form_fill = self._build_form_fill_suggestion(basic_info, skills, projects, internships, campus, certificates, innovation, pending_fields)

        return ResumeStructuredProfile(
            basic_info=basic_info,
            skills=skills,
            project_experiences=projects,
            internship_experiences=internships,
            campus_experiences=campus,
            certificates=certificates,
            innovation_indicators=innovation,
            pending_fields=pending_fields,
            extraction_notes=notes,
            form_fill_suggestion=form_fill,
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        return text.replace('\r\n', '\n').replace('\r', '\n').replace('\t', ' ').strip()

    @staticmethod
    def _split_lines(text: str) -> list[str]:
        raw_lines = [line.strip(' \u3000•·-') for line in text.split('\n')]
        return [line.strip() for line in raw_lines if line.strip()]

    def _split_sections(self, lines: list[str]) -> dict[str, list[str]]:
        sections: dict[str, list[str]] = defaultdict(list)
        current_section = 'general'
        for line in lines:
            heading = self._detect_section_heading(line)
            if heading:
                current_section = heading
                continue
            sections[current_section].append(line)
        return dict(sections)

    def _detect_section_heading(self, line: str) -> Optional[str]:
        normalized = line.strip('：: ').replace(' ', '')
        if len(normalized) > 18:
            return None
        for keyword, section in self.SECTION_ALIASES.items():
            if normalized == keyword or normalized.startswith(keyword):
                return section
        return None

    def _extract_basic_info(self, lines: list[str], sections: dict[str, list[str]]) -> ResumeBasicInfo:
        education_lines = sections.get('education', [])
        combined_text = '\n'.join(lines)
        name = self._extract_name(lines)
        school = self._extract_school(education_lines or lines)
        major = self._extract_major(education_lines or lines)
        degree = self._extract_degree(education_lines or lines)
        graduation_year = self._extract_graduation_year(education_lines or lines, combined_text)
        return ResumeBasicInfo(
            name=name,
            school=school,
            major=major,
            degree=degree,
            graduation_year=graduation_year,
        )

    def _extract_name(self, lines: list[str]) -> ResumeExtractionField:
        for line in lines[:8]:
            match = re.search(r'(?:姓名|Name)[:： ]*([A-Za-z\u4e00-\u9fa5·]{2,20})', line)
            if match:
                return self._make_field(match.group(1), 0.98, line, 'explicit_name_label')
        for line in lines[:5]:
            if self.PHONE_PATTERN.search(line) or self.EMAIL_PATTERN.search(line):
                continue
            if 1 < len(line) <= 8 and re.fullmatch(r'[A-Za-z\u4e00-\u9fa5· ]{2,20}', line):
                return self._make_field(line, 0.62, line, 'first_line_heuristic')
        return self._make_field('', 0.0, '', 'name_not_found', status='pending_confirmation', reason='未从简历中稳定识别到姓名')

    def _extract_school(self, lines: list[str]) -> ResumeExtractionField:
        for line in lines:
            explicit = re.search(r'(?:学校|院校|毕业院校)[:： ]*([^，,；;\n]+)', line)
            if explicit:
                value = explicit.group(1).strip()
                return self._make_field(value, 0.95, line, 'explicit_school_label')
            match = self.SCHOOL_PATTERN.search(line)
            if match:
                return self._make_field(match.group(1), 0.82, line, 'school_pattern')
        return self._make_field('', 0.0, '', 'school_not_found', status='pending_confirmation', reason='学校信息缺失或表达不规范')

    def _extract_major(self, lines: list[str]) -> ResumeExtractionField:
        for line in lines:
            explicit = re.search(r'(?:专业|主修)[:： ]*([^，,；;\n]+)', line)
            if explicit:
                return self._make_field(explicit.group(1).strip(), 0.95, line, 'explicit_major_label')
            if self.SCHOOL_PATTERN.search(line):
                cleaned = self.SCHOOL_PATTERN.sub('', line)
                cleaned = re.sub(r'20\d{2}[^\u4e00-\u9fa5A-Za-z]*', ' ', cleaned)
                cleaned = re.sub('|'.join(self.DEGREE_ORDER), ' ', cleaned)
                candidate = re.sub(r'\s+', ' ', cleaned).strip(' -|/')
                if 1 < len(candidate) <= 20 and not self.TIME_RANGE_PATTERN.search(candidate):
                    return self._make_field(candidate, 0.68, line, 'education_line_major_heuristic')
        return self._make_field('', 0.0, '', 'major_not_found', status='pending_confirmation', reason='专业信息未明确识别')

    def _extract_degree(self, lines: list[str]) -> ResumeExtractionField:
        for degree in self.DEGREE_ORDER:
            for line in lines:
                if degree in line:
                    confidence = 0.95 if re.search(r'(?:学历|学位)[:： ]*', line) else 0.82
                    reason = 'explicit_degree_label' if confidence > 0.9 else 'degree_keyword_match'
                    return self._make_field(degree, confidence, line, reason)
        return self._make_field('', 0.0, '', 'degree_not_found', status='pending_confirmation', reason='学历字段未识别')

    def _extract_graduation_year(self, lines: list[str], full_text: str) -> ResumeExtractionField:
        for line in lines:
            explicit = re.search(r'(?:毕业时间|毕业年份|预计毕业|毕业)[:： ]*(20\d{2})', line)
            if explicit:
                return self._make_field(explicit.group(1), 0.95, line, 'explicit_graduation_year')
        years = [match.group(1) for match in self.GRAD_YEAR_PATTERN.finditer(full_text)]
        if years:
            return self._make_field(sorted(years)[-1], 0.65, full_text[:120], 'latest_year_heuristic')
        return self._make_field('', 0.0, '', 'graduation_year_not_found', status='pending_confirmation', reason='毕业年份未明确标注')

    def _extract_skills(self, lines: list[str], sections: dict[str, list[str]]) -> ResumeStructuredSkills:
        relevant_lines = sections.get('skills', []) + sections.get('project', []) + sections.get('internship', []) + lines[:20]
        matched: dict[str, ResumeSkillItem] = {}
        unmatched_candidates: list[str] = []
        for line in relevant_lines:
            line_lower = line.lower()
            for alias, canonical in self.skill_alias_map.items():
                if self._contains_skill(line_lower, alias):
                    current = matched.get(canonical)
                    confidence = 0.95 if line in sections.get('skills', []) else 0.78
                    if current is None or confidence > current.confidence:
                        matched[canonical] = ResumeSkillItem(
                            canonical_name=canonical,
                            category=self._skill_category(canonical),
                            matched_alias=alias,
                            confidence=confidence,
                            source_excerpt=line[:160],
                        )
            if line in sections.get('skills', []):
                tokens = re.split(r'[、,，/|；; ]+', line)
                for token in tokens:
                    candidate = token.strip()
                    if 1 < len(candidate) <= 20 and not self._is_noise_token(candidate) and not self._match_known_skill(candidate):
                        unmatched_candidates.append(candidate)

        ordered_items = sorted(matched.values(), key=lambda item: (item.category, item.canonical_name.lower()))
        programming_languages = [item.canonical_name for item in ordered_items if item.category == 'programming_language']
        frameworks = [item.canonical_name for item in ordered_items if item.category == 'framework']
        tools = [item.canonical_name for item in ordered_items if item.category == 'tool']
        return ResumeStructuredSkills(
            programming_languages=programming_languages,
            frameworks=frameworks,
            tools=tools,
            matched_skills=ordered_items,
            unmatched_candidates=self._unique(unmatched_candidates)[:8],
        )

    def _extract_projects(self, sections: dict[str, list[str]], skills: ResumeStructuredSkills) -> list[ResumeExperienceItem]:
        source_lines = sections.get('project', [])
        return self._extract_experience_blocks(source_lines, 'project', skills)

    def _extract_internships(self, sections: dict[str, list[str]], skills: ResumeStructuredSkills) -> list[ResumeExperienceItem]:
        source_lines = sections.get('internship', [])
        return self._extract_experience_blocks(source_lines, 'internship', skills)

    def _extract_campus_experiences(self, sections: dict[str, list[str]], skills: ResumeStructuredSkills) -> list[ResumeExperienceItem]:
        source_lines = sections.get('campus', [])
        return self._extract_experience_blocks(source_lines, 'campus', skills)

    def _extract_experience_blocks(
        self,
        lines: list[str],
        item_type: str,
        skills: ResumeStructuredSkills,
    ) -> list[ResumeExperienceItem]:
        if not lines:
            return []
        blocks = self._group_blocks(lines, item_type)
        items: list[ResumeExperienceItem] = []
        known_skills = {item.canonical_name for item in skills.matched_skills}
        for block in blocks:
            text = ' | '.join(block)
            title = self._extract_block_title(block, item_type)
            organization = self._extract_organization(text, item_type)
            role = self._extract_role(text, item_type)
            time_range = self._extract_time_range(text)
            tech_stack = sorted(set(self._match_skills_from_text(text)) | set(skill for skill in known_skills if self._contains_skill(text.lower(), self._normalize_alias(skill))))
            achievements = self._extract_achievements(block, item_type)
            confidence = self._average([
                0.78 if title else 0.0,
                0.8 if organization else 0.0,
                0.72 if role else 0.0,
                0.75 if time_range else 0.0,
                0.82 if text else 0.0,
            ])
            pending_fields: list[str] = []
            if item_type == 'project' and not title:
                pending_fields.append('title')
            if item_type in {'internship', 'campus'} and not organization:
                pending_fields.append('organization')
            if not role:
                pending_fields.append('role')
            if item_type == 'project' and not tech_stack:
                pending_fields.append('tech_stack')
            items.append(
                ResumeExperienceItem(
                    item_type=item_type,
                    title=title,
                    organization=organization,
                    role=role,
                    time_range=time_range,
                    description=text[:320],
                    tech_stack=tech_stack,
                    achievements=achievements,
                    confidence=round(confidence, 2),
                    pending_fields=pending_fields,
                    source_excerpt=text[:220],
                )
            )
        return items[:6]

    def _group_blocks(self, lines: list[str], item_type: str) -> list[list[str]]:
        blocks: list[list[str]] = []
        current: list[str] = []
        for line in lines:
            if not current:
                current = [line]
                continue
            should_break = False
            if self.TIME_RANGE_PATTERN.search(line):
                should_break = True
            elif self._looks_like_title_line(line, item_type) and not self._starts_with_detail_prefix(line):
                should_break = True
            if should_break:
                blocks.append(current)
                current = [line]
            else:
                current.append(line)
        if current:
            blocks.append(current)
        return blocks

    def _looks_like_title_line(self, line: str, item_type: str) -> bool:
        text = line.strip()
        if len(text) > 36:
            return False
        if item_type == 'project' and any(hint in text for hint in self.PROJECT_TITLE_HINTS):
            return True
        if item_type == 'internship' and re.search(r'(公司|科技|信息|网络|软件|银行|集团|有限公司)', text):
            return True
        if item_type == 'campus' and re.search(r'(学生会|社团|协会|实验室|班级|志愿|竞赛)', text):
            return True
        return False

    def _starts_with_detail_prefix(self, line: str) -> bool:
        return any(line.startswith(prefix) for prefix in self.DETAIL_PREFIXES)

    def _extract_block_title(self, block: list[str], item_type: str) -> str:
        first_line = block[0]
        explicit = re.search(r'(?:项目名称|项目|活动)[:： ]*([^|；;]+)', first_line)
        if explicit and len(explicit.group(1).strip()) <= 40:
            return explicit.group(1).strip()
        cleaned = self.TIME_RANGE_PATTERN.sub('', first_line)
        cleaned = re.sub(r'^\d+[.、]\s*', '', cleaned).strip(' -|/')
        if item_type == 'project' and any(hint in cleaned for hint in self.PROJECT_TITLE_HINTS):
            return cleaned[:40]
        if item_type == 'campus' and re.search(r'(学生会|社团|协会|实验室|班级|志愿|竞赛)', cleaned):
            return cleaned[:40]
        return cleaned[:40] if len(cleaned) <= 24 and not self._starts_with_detail_prefix(cleaned) else ''

    def _extract_organization(self, text: str, item_type: str) -> str:
        if item_type == 'project':
            return ''
        explicit = re.search(r'(?:公司|单位|组织|部门|机构)[:： ]*([^|；;]+)', text)
        if explicit:
            return explicit.group(1).strip()
        if item_type == 'internship':
            company = re.search(r'([A-Za-z0-9\u4e00-\u9fa5·()（）-]{2,40}(?:公司|集团|科技|信息|网络|软件|银行|有限公司))', text)
            if company:
                return company.group(1)
        if item_type == 'campus':
            campus = re.search(r'([A-Za-z0-9\u4e00-\u9fa5·()（）-]{2,30}(?:学生会|社团|协会|实验室|班级|志愿队|竞赛队))', text)
            if campus:
                return campus.group(1)
        return ''

    def _extract_role(self, text: str, item_type: str) -> str:
        explicit = re.search(r'(?:角色|岗位|职位|担任|任职)[:： ]*([^|；;]+)', text)
        if explicit:
            return explicit.group(1).strip()[:40]
        if item_type == 'internship':
            title = re.search(r'((?:开发|测试|产品|运营|算法|数据|前端|后端).{0,8}(?:工程师|实习生|助理))', text)
            if title:
                return title.group(1).strip()
        if '负责' in text:
            snippet = text.split('负责', 1)[1]
            return ('负责' + snippet[:22]).strip(' |；;，,')
        role = re.search(r'(主席|部长|负责人|组长|班长|委员|干事|队长)', text)
        return role.group(1) if role else ''

    def _extract_time_range(self, text: str) -> str:
        match = self.TIME_RANGE_PATTERN.search(text)
        return match.group(1) if match else ''

    def _extract_achievements(self, block: list[str], item_type: str) -> list[str]:
        hints = self.AWARD_HINTS if item_type == 'campus' else ('提升', '优化', '完成', '负责', '获奖', '上线')
        result: list[str] = []
        for line in block:
            if any(hint in line for hint in hints):
                result.append(line[:120])
        return self._unique(result)[:3]

    def _extract_certificates(self, lines: list[str], sections: dict[str, list[str]]) -> list[ResumeCertificateItem]:
        source_lines = sections.get('certificate', []) or [line for line in lines if any(hint in line for hint in self.CERTIFICATE_HINTS)]
        items: list[ResumeCertificateItem] = []
        for line in source_lines:
            candidates = [segment.strip() for segment in re.split(r'[、,，；;|/]', line) if segment.strip()]
            for candidate in candidates:
                if not any(hint in candidate for hint in self.CERTIFICATE_HINTS):
                    continue
                year_match = self.GRAD_YEAR_PATTERN.search(candidate)
                items.append(
                    ResumeCertificateItem(
                        name=re.sub(r'(?:获得时间|时间)[:： ]*20\d{2}.*$', '', candidate).strip()[:40],
                        obtained_at=year_match.group(1) if year_match else '',
                        confidence=0.88 if year_match else 0.76,
                        source_excerpt=line[:160],
                        pending_fields=[] if year_match else ['obtained_at'],
                    )
                )
        deduped: list[ResumeCertificateItem] = []
        seen: set[str] = set()
        for item in items:
            if item.name and item.name not in seen:
                seen.add(item.name)
                deduped.append(item)
        return deduped[:6]

    def _extract_innovation(self, lines: list[str], sections: dict[str, list[str]]) -> ResumeInnovationIndicators:
        award_lines = sections.get('award', []) + [line for line in lines if any(hint in line for hint in self.AWARD_HINTS)]
        innovation_lines = sections.get('innovation', []) + sections.get('project', []) + sections.get('campus', [])
        award_items = self._unique([line[:120] for line in award_lines if any(hint in line for hint in self.AWARD_HINTS)])[:5]
        patent_items = self._unique([line[:120] for line in innovation_lines if any(hint in line for hint in self.PATENT_HINTS)])[:5]
        publication_items = self._unique([line[:120] for line in innovation_lines if any(hint in line for hint in self.PUBLICATION_HINTS)])[:5]
        entrepreneurship_items = self._unique([line[:120] for line in innovation_lines if any(hint in line for hint in self.ENTREPRENEURSHIP_HINTS)])[:5]
        return ResumeInnovationIndicators(
            has_awards=bool(award_items),
            has_patents=bool(patent_items),
            has_publications=bool(publication_items),
            has_entrepreneurship=bool(entrepreneurship_items),
            award_items=award_items,
            patent_items=patent_items,
            publication_items=publication_items,
            entrepreneurship_items=entrepreneurship_items,
        )

    def _collect_pending_fields(
        self,
        basic_info: ResumeBasicInfo,
        projects: list[ResumeExperienceItem],
        internships: list[ResumeExperienceItem],
        campus: list[ResumeExperienceItem],
        certificates: list[ResumeCertificateItem],
    ) -> list[ResumePendingField]:
        pending: list[ResumePendingField] = []
        for field_name, label in [('name', '姓名'), ('school', '学校'), ('major', '专业'), ('degree', '学历'), ('graduation_year', '毕业年份')]:
            field = getattr(basic_info, field_name)
            if field.status != 'confirmed':
                pending.append(ResumePendingField(field_path=f'basic_info.{field_name}', label=label, reason=field.reason or '待确认'))
        for index, item in enumerate(projects):
            for field_name in item.pending_fields:
                pending.append(ResumePendingField(field_path=f'project_experiences[{index}].{field_name}', label=f'项目经历 {index + 1} / {field_name}', reason='项目字段未完全识别'))
        for index, item in enumerate(internships):
            for field_name in item.pending_fields:
                pending.append(ResumePendingField(field_path=f'internship_experiences[{index}].{field_name}', label=f'实习经历 {index + 1} / {field_name}', reason='实习字段需要用户确认'))
        for index, item in enumerate(campus):
            for field_name in item.pending_fields:
                pending.append(ResumePendingField(field_path=f'campus_experiences[{index}].{field_name}', label=f'校园经历 {index + 1} / {field_name}', reason='校园经历字段需要确认'))
        for index, item in enumerate(certificates):
            for field_name in item.pending_fields:
                pending.append(ResumePendingField(field_path=f'certificates[{index}].{field_name}', label=f'证书 {index + 1} / {field_name}', reason='证书时间缺失'))
        return pending

    def _build_notes(
        self,
        file_name: str,
        sections: dict[str, list[str]],
        projects: list[ResumeExperienceItem],
        internships: list[ResumeExperienceItem],
        campus: list[ResumeExperienceItem],
    ) -> list[str]:
        notes = [f'文件：{file_name or "unknown"}']
        notes.append(f'识别 section：{", ".join(sorted(sections.keys())) or "general"}')
        notes.append(f'项目 {len(projects)} 条 / 实习 {len(internships)} 条 / 校园经历 {len(campus)} 条')
        return notes

    def _build_form_fill_suggestion(
        self,
        basic_info: ResumeBasicInfo,
        skills: ResumeStructuredSkills,
        projects: list[ResumeExperienceItem],
        internships: list[ResumeExperienceItem],
        campus: list[ResumeExperienceItem],
        certificates: list[ResumeCertificateItem],
        innovation: ResumeInnovationIndicators,
        pending_fields: list[ResumePendingField],
    ) -> ResumeFormFillSuggestion:
        skill_list = self._unique(skills.programming_languages + skills.frameworks + skills.tools)
        project_lines = [self._format_experience_line(item, include_org=False) for item in projects]
        internship_lines = [self._format_experience_line(item, include_org=True) for item in internships]
        campus_lines = [self._format_experience_line(item, include_org=True) for item in campus]
        certificate_names = [item.name for item in certificates if item.name]
        summary_parts: list[str] = []
        if innovation.has_awards:
            summary_parts.append('包含获奖经历')
        if innovation.has_patents:
            summary_parts.append('包含专利成果')
        if innovation.has_publications:
            summary_parts.append('包含论文/发表经历')
        if innovation.has_entrepreneurship:
            summary_parts.append('包含创业经历')
        return ResumeFormFillSuggestion(
            name=basic_info.name.value,
            school=basic_info.school.value,
            major=basic_info.major.value,
            degree=basic_info.degree.value,
            graduation_year=int(basic_info.graduation_year.value) if basic_info.graduation_year.value.isdigit() else None,
            manual_skills=skill_list,
            project_experiences=project_lines,
            internship_experiences=internship_lines,
            campus_experiences=campus_lines,
            certificates=certificate_names,
            self_description='；'.join(summary_parts),
            pending_prompts=[f'{item.label}：{item.reason}' for item in pending_fields],
        )

    def _build_skill_alias_map(self, lexicon: list[str]) -> dict[str, str]:
        alias_map: dict[str, str] = {}
        for skill in lexicon:
            alias_map[self._normalize_alias(skill)] = skill
            alias_map[skill.lower()] = skill
        for alias, canonical in self.SKILL_ALIASES.items():
            alias_map[self._normalize_alias(alias)] = canonical
            alias_map[alias.lower()] = canonical
        return alias_map

    @staticmethod
    def _normalize_alias(text: str) -> str:
        return re.sub(r'[^a-z0-9\u4e00-\u9fa5#+]', '', text.lower())

    def _match_skills_from_text(self, text: str) -> list[str]:
        lower_text = text.lower()
        matched: list[str] = []
        for alias, canonical in self.skill_alias_map.items():
            if self._contains_skill(lower_text, alias) and canonical not in matched:
                matched.append(canonical)
        return matched

    def _match_known_skill(self, token: str) -> bool:
        normalized = self._normalize_alias(token)
        return normalized in self.skill_alias_map or token.lower() in self.skill_alias_map

    @staticmethod
    def _contains_skill(text: str, alias: str) -> bool:
        if not alias:
            return False
        compact_text = re.sub(r'[^a-z0-9\u4e00-\u9fa5#+]', '', text.lower())
        if re.fullmatch(r'[a-z0-9#+]{1,3}', alias):
            return bool(re.search(rf'(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])', text.lower()))
        return alias in compact_text or alias in text.lower()

    def _skill_category(self, skill: str) -> str:
        if skill in self.LANGUAGE_SKILLS:
            return 'programming_language'
        if skill in self.FRAMEWORK_SKILLS:
            return 'framework'
        return 'tool'

    @staticmethod
    def _make_field(
        value: str,
        confidence: float,
        source_excerpt: str,
        reason: str,
        status: Optional[str] = None,
        reason_text: str = '',
    ) -> ResumeExtractionField:
        effective_status = status or ('confirmed' if value and confidence >= 0.8 else 'pending_confirmation')
        return ResumeExtractionField(
            value=value.strip(),
            status=effective_status,
            confidence=round(confidence, 2),
            source_excerpt=source_excerpt[:180],
            reason=reason_text or reason,
        )

    @staticmethod
    def _format_experience_line(item: ResumeExperienceItem, include_org: bool) -> str:
        pieces: list[str] = []
        if item.organization and include_org:
            pieces.append(item.organization)
        if item.title:
            pieces.append(item.title)
        if item.role:
            pieces.append(item.role)
        if item.time_range:
            pieces.append(item.time_range)
        if item.tech_stack:
            pieces.append('Tech: ' + ', '.join(item.tech_stack))
        pieces.append(item.description)
        return ' | '.join(piece for piece in pieces if piece)

    @staticmethod
    def _average(values: list[float]) -> float:
        real_values = [value for value in values if value > 0]
        if not real_values:
            return 0.0
        return sum(real_values) / len(real_values)

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

    @staticmethod
    def _is_noise_token(token: str) -> bool:
        return bool(re.fullmatch(r'(技能|熟悉|掌握|了解|使用|项目|经历|负责)', token))
