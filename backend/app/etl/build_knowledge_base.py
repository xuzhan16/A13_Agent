import argparse
import hashlib
import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import xlrd

from backend.app.core.catalog import JOB_FAMILY_BY_NAME, JOB_FAMILY_TEMPLATES
from backend.app.schemas.graph import JobGraph, JobGraphEdge, JobGraphNode

RAW_FIELD_INDEX = {
    'job_title': 0,
    'address': 1,
    'salary_range': 2,
    'company_name': 3,
    'industry': 4,
    'company_scale': 5,
    'company_type': 6,
    'job_code': 7,
    'job_detail': 8,
    'updated_at': 9,
    'company_detail': 10,
    'source_url': 11,
}

MAJOR_LEXICON = [
    '计算机科学与技术', '软件工程', '信息工程', '通信工程', '电子信息', '自动化',
    '网络工程', '信息管理', '地理信息', '测绘工程', '数字媒体技术', '工业工程',
    '管理学', '市场营销', '工商管理', '计算机',
]

CERTIFICATE_LEXICON = [
    '英语四级', '英语六级', '软考中级', '软考高级', 'PMP', 'ISTQB', '计算机二级',
]

ADDITIONAL_HARD_SKILLS = [
    'Python', 'SQL', 'Redis', 'Linux', 'Oracle', 'ArcGIS', 'Spring', 'Spring Boot',
    'MySQL', 'Postman', 'JMeter', 'Selenium', 'Vue', 'React', 'TypeScript', 'Webpack',
    'JavaScript', 'HTML', 'CSS', 'AUTOSAR', 'CAN', 'C语言', 'C++', '嵌入式开发', '示波器',
    '需求分析', '原型设计', 'Axure', 'Figma', 'Jira', '项目管理', '接口测试', '自动化测试',
    '性能测试', '数据分析', '方案设计', '招投标', '网络排障', '微服务', '消息队列',
    '数据结构', '接口设计', '系统部署', '问题排查', '客户沟通', '文档编写',
]

ADDITIONAL_SOFT_SKILLS = [
    '学习能力', '沟通能力', '抗压能力', '团队协作', '责任心', '执行力', '同理心',
    '推动力', '领导力', '耐心', '细致严谨', '服务意识', '应变能力', '逻辑思维',
    '动手能力', '问题定位能力',
]

TECH_CONTEXT_KEYWORDS = [
    '计算机', '软件', '系统', '信息化', '互联网', '网络', '数据库', '服务器', '平台',
    '程序', '开发', '调试', '自动化', 'Java', 'Python', '前端', '后端', '测试', '硬件',
    '物联网', 'GIS', 'Linux', 'Oracle', 'MySQL', '芯片', '半导体', '云', '接口', '运维',
]

GENERIC_SNIPPETS = {'岗位要求', '岗位职责', '职位描述', '任职要求', '工作内容'}
GENERIC_JOB_FAMILIES = {'技术支持工程师', '实施工程师', '项目经理', '销售工程师', '产品专员'}
ASCII_TERM_RE = re.compile(r'^[a-z0-9+.#/\- ]+$')
HTML_TAG_RE = re.compile(r'<[^>]+>')
SPACE_RE = re.compile(r'\s+')
SALARY_SPLIT_RE = re.compile(r'[-~至]')


def clean_text(value: object) -> str:
    if value is None:
        return ''
    text = str(value).replace('\xa0', ' ')
    text = html.unescape(text)
    text = text.replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')
    text = HTML_TAG_RE.sub(' ', text)
    text = SPACE_RE.sub(' ', text)
    return text.strip()


def normalize_title(value: str) -> str:
    return clean_text(value).lower().replace(' ', '')


def extract_city(address: str) -> str:
    text = clean_text(address)
    if not text:
        return ''
    return re.split(r'[-·]', text)[0].strip()


def split_industries(industry_text: str) -> list[str]:
    text = clean_text(industry_text)
    if not text:
        return []
    return [item.strip() for item in re.split(r'[,，/、]+', text) if item.strip()]


def infer_number(token: str, context: str) -> Optional[float]:
    token = token.lower().strip()
    match = re.search(r'(\d+(?:\.\d+)?)', token)
    if not match:
        return None
    value = float(match.group(1))
    if '万' in token or ('万' in context and '千' not in token and 'k' not in token):
        return value * 10000
    if '千' in token or 'k' in token:
        return value * 1000
    return value


def parse_salary_range(value: str) -> tuple[Optional[float], Optional[float]]:
    text = clean_text(value).lower().replace(' ', '')
    if not text:
        return (None, None)
    text = text.split('·')[0]
    daily = '/天' in text or '元/天' in text
    parts = SALARY_SPLIT_RE.split(text)
    if len(parts) < 2:
        return (None, None)
    low = infer_number(parts[0], text)
    high = infer_number(parts[1], text)
    if low is None or high is None:
        return (None, None)
    if daily:
        low *= 21.75
        high *= 21.75
    return (round(low, 2), round(high, 2))


def unique_preserve(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def contains_term(text: str, term: str) -> bool:
    lowered = text.lower()
    normalized_term = term.lower()
    if ASCII_TERM_RE.fullmatch(normalized_term):
        pattern = re.compile(r'(?<![a-z0-9])' + re.escape(normalized_term) + r'(?![a-z0-9])')
        return bool(pattern.search(lowered))
    return normalized_term in lowered


def pick_terms(base_terms: Iterable[str], observed_counter: Counter, limit: int, min_count: int = 1) -> list[str]:
    selected: list[str] = []
    for term in base_terms:
        if observed_counter.get(term, 0) > 0:
            selected.append(term)
    for term, count in observed_counter.most_common():
        if count >= min_count:
            selected.append(term)
    for term in base_terms:
        selected.append(term)
    return unique_preserve(selected)[:limit]


def percentile(values: list[float], ratio: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    index = min(int((len(ordered) - 1) * ratio), len(ordered) - 1)
    return round(ordered[index], 2)


def standardize_job_family(job_title: str) -> Optional[str]:
    normalized = normalize_title(job_title)
    if not normalized:
        return None
    for template in JOB_FAMILY_TEMPLATES:
        for alias in template.aliases:
            if alias.lower().replace(' ', '') in normalized:
                return template.job_family
    return None


def build_skill_lexicon() -> list[str]:
    terms: list[str] = []
    for template in JOB_FAMILY_TEMPLATES:
        terms.extend(template.required_skills)
        terms.extend(template.bonus_skills)
    terms.extend(ADDITIONAL_HARD_SKILLS)
    return unique_preserve(terms)


def build_soft_skill_lexicon() -> list[str]:
    terms: list[str] = []
    for template in JOB_FAMILY_TEMPLATES:
        terms.extend(template.soft_skills)
    terms.extend(ADDITIONAL_SOFT_SKILLS)
    return unique_preserve(terms)


def count_terms(texts: list[str], lexicon: list[str]) -> Counter:
    counter: Counter = Counter()
    for text in texts:
        lowered = text.lower()
        for term in lexicon:
            if contains_term(lowered, term):
                counter[term] += 1
    return counter


def build_evidence_snippets(rows: list[dict]) -> list[str]:
    snippets: list[str] = []
    for row in rows:
        text = row['job_detail']
        if not text or len(text) < 20:
            continue
        if text in GENERIC_SNIPPETS:
            continue
        if any(text.startswith(prefix) for prefix in GENERIC_SNIPPETS) and len(text) < 40:
            continue
        snippets.append(text[:140])
    return unique_preserve(snippets)[:3]


def derive_practice_requirements(job_family: str, texts: list[str], defaults: tuple[str, ...]) -> list[str]:
    corpus = ' '.join(texts)
    requirements = list(defaults)
    if '实习' in corpus or '项目' in corpus:
        requirements.append('具备项目或实习实践经历')
    if '出差' in corpus or '驻场' in corpus:
        requirements.append('接受客户现场支持或出差场景')
    if '作品' in corpus or '展示' in corpus:
        requirements.append('可展示作品、项目成果或交付材料')
    if job_family in {'实施工程师', '技术支持工程师', '销售工程师'} and '客户' in corpus:
        requirements.append('具备客户沟通与需求理解能力')
    return unique_preserve(requirements)[:4]


def is_relevant_row(row: dict, job_family: str) -> bool:
    if job_family not in GENERIC_JOB_FAMILIES:
        return True
    template = JOB_FAMILY_BY_NAME[job_family]
    corpus = ' '.join([
        row['job_title'], row['industry_text'], row['job_detail'], row['company_detail'],
    ])
    if any(contains_term(corpus, keyword) for keyword in TECH_CONTEXT_KEYWORDS):
        return True
    family_keywords = list(template.required_skills) + list(template.bonus_skills) + list(template.preferred_majors)
    return any(contains_term(corpus, keyword) for keyword in family_keywords)


class JobKnowledgeBuilder:
    def __init__(self, input_path: str, output_dir: str) -> None:
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.hard_skill_lexicon = build_skill_lexicon()
        self.soft_skill_lexicon = build_soft_skill_lexicon()

    def build(self) -> dict:
        raw_rows = self._load_rows()
        deduped_rows = self._deduplicate_rows(raw_rows)
        standardized_rows, ignored_rows = self._standardize_rows(deduped_rows)
        profiles = self._build_profiles(standardized_rows)
        graph = self._build_graph(profiles)
        report = self._build_report(raw_rows, deduped_rows, standardized_rows, ignored_rows, profiles)
        self._write_outputs(standardized_rows, profiles, graph, report)
        return report

    def _load_rows(self) -> list[dict]:
        book = xlrd.open_workbook(str(self.input_path))
        sheet = book.sheet_by_index(0)
        rows: list[dict] = []
        for row_index in range(1, sheet.nrows):
            row_values = sheet.row_values(row_index)
            job_title = clean_text(row_values[RAW_FIELD_INDEX['job_title']])
            address = clean_text(row_values[RAW_FIELD_INDEX['address']])
            salary_text = clean_text(row_values[RAW_FIELD_INDEX['salary_range']])
            company_name = clean_text(row_values[RAW_FIELD_INDEX['company_name']])
            industry_text = clean_text(row_values[RAW_FIELD_INDEX['industry']])
            job_code = clean_text(row_values[RAW_FIELD_INDEX['job_code']])
            job_detail = clean_text(row_values[RAW_FIELD_INDEX['job_detail']])
            company_detail = clean_text(row_values[RAW_FIELD_INDEX['company_detail']])
            source_url = clean_text(row_values[RAW_FIELD_INDEX['source_url']])
            salary_min, salary_max = parse_salary_range(salary_text)
            rows.append(
                {
                    'job_title': job_title,
                    'address': address,
                    'city': extract_city(address),
                    'salary_text': salary_text,
                    'salary_min_monthly': salary_min,
                    'salary_max_monthly': salary_max,
                    'company_name': company_name,
                    'industry_text': industry_text,
                    'industries': split_industries(industry_text),
                    'company_scale': clean_text(row_values[RAW_FIELD_INDEX['company_scale']]),
                    'company_type': clean_text(row_values[RAW_FIELD_INDEX['company_type']]),
                    'job_code': job_code,
                    'job_detail': job_detail,
                    'updated_at': clean_text(row_values[RAW_FIELD_INDEX['updated_at']]),
                    'company_detail': company_detail,
                    'source_url': source_url,
                }
            )
        return rows

    def _deduplicate_rows(self, rows: list[dict]) -> list[dict]:
        deduped: list[dict] = []
        seen: set[str] = set()
        for row in rows:
            candidate = row['job_code'] or row['source_url']
            if not candidate:
                raw = '||'.join([
                    row['job_title'], row['company_name'], row['job_detail'], row['salary_text'], row['address'],
                ])
                candidate = hashlib.sha1(raw.encode('utf-8')).hexdigest()
            if candidate in seen:
                continue
            seen.add(candidate)
            deduped.append(row)
        return deduped

    def _standardize_rows(self, rows: list[dict]) -> tuple[list[dict], list[dict]]:
        kept: list[dict] = []
        ignored: list[dict] = []
        for row in rows:
            family = standardize_job_family(row['job_title'])
            if family is None or not is_relevant_row(row, family):
                ignored.append(row)
                continue
            normalized = dict(row)
            normalized['job_family'] = family
            kept.append(normalized)
        return kept, ignored

    def _build_profiles(self, rows: list[dict]) -> list[dict]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            grouped[row['job_family']].append(row)

        profiles: list[dict] = []
        for job_family, family_rows in grouped.items():
            template = JOB_FAMILY_BY_NAME[job_family]
            texts = [row['job_detail'] for row in family_rows] + [row['company_detail'] for row in family_rows]
            hard_counter = count_terms(texts, self.hard_skill_lexicon)
            soft_counter = count_terms(texts, self.soft_skill_lexicon)
            major_counter = count_terms(texts, MAJOR_LEXICON)
            certificate_counter = count_terms(texts, CERTIFICATE_LEXICON)
            title_counter = Counter(row['job_title'] for row in family_rows)
            city_counter = Counter(row['city'] for row in family_rows if row['city'])
            industry_counter: Counter = Counter()
            for row in family_rows:
                industry_counter.update(row['industries'])

            required_skills = pick_terms(template.required_skills, hard_counter, limit=6, min_count=2)
            bonus_skills = [
                item for item in pick_terms(template.bonus_skills, hard_counter, limit=6, min_count=1)
                if item not in required_skills
            ][:6]

            salary_lows = [row['salary_min_monthly'] for row in family_rows if row['salary_min_monthly'] is not None]
            salary_highs = [row['salary_max_monthly'] for row in family_rows if row['salary_max_monthly'] is not None]

            profile = {
                'job_family': job_family,
                'description': template.description,
                'preferred_majors': pick_terms(template.preferred_majors, major_counter, limit=5, min_count=1),
                'required_skills': required_skills,
                'bonus_skills': bonus_skills,
                'soft_skills': pick_terms(template.soft_skills, soft_counter, limit=5, min_count=1),
                'certificates': pick_terms(template.certificates, certificate_counter, limit=3, min_count=1),
                'practice_requirements': derive_practice_requirements(job_family, texts, template.practice_requirements),
                'vertical_growth_path': list(template.vertical_growth_path),
                'transfer_paths': list(template.transfer_paths),
                'aliases': list(template.aliases),
                'source_titles': [item for item, _ in title_counter.most_common(5)],
                'sample_count': len(family_rows),
                'top_cities': [item for item, _ in city_counter.most_common(5)],
                'top_industries': [item for item, _ in industry_counter.most_common(5)],
                'salary_min_monthly': percentile(salary_lows, 0.25),
                'salary_max_monthly': percentile(salary_highs, 0.75),
                'evidence_snippets': build_evidence_snippets(family_rows),
            }
            profiles.append(profile)
        profiles.sort(key=lambda item: item['sample_count'], reverse=True)
        return profiles

    def _build_graph(self, profiles: list[dict]) -> dict:
        profile_by_name = {item['job_family']: item for item in profiles}
        nodes: list[JobGraphNode] = []
        edges: list[JobGraphEdge] = []
        node_ids: set[str] = set()

        def add_node(node_id: str, label: str, node_type: str, sample_count: int = 0, top_skills: Optional[list[str]] = None, top_cities: Optional[list[str]] = None) -> None:
            if node_id in node_ids:
                return
            node_ids.add(node_id)
            nodes.append(
                JobGraphNode(
                    id=node_id,
                    label=label,
                    node_type=node_type,
                    sample_count=sample_count,
                    top_skills=top_skills or [],
                    top_cities=top_cities or [],
                )
            )

        for profile in profiles:
            add_node(
                node_id=profile['job_family'],
                label=profile['job_family'],
                node_type='job_family',
                sample_count=profile['sample_count'],
                top_skills=profile['required_skills'][:4],
                top_cities=profile['top_cities'][:3],
            )

        for profile in profiles:
            previous = profile['job_family']
            for role in profile['vertical_growth_path'][1:]:
                add_node(node_id=role, label=role, node_type='career_stage')
                edges.append(
                    JobGraphEdge(
                        source=previous,
                        target=role,
                        edge_type='vertical',
                        weight=1.0,
                        reason='基于岗位标准晋升路径构建的纵向发展边。',
                    )
                )
                previous = role

            current_skills = set(profile['required_skills'] + profile['bonus_skills'])
            for target in profile['transfer_paths']:
                target_profile = profile_by_name.get(target)
                if target_profile is not None:
                    target_skills = set(target_profile['required_skills'] + target_profile['bonus_skills'])
                    union = current_skills | target_skills
                    overlap = round(len(current_skills & target_skills) / len(union), 2) if union else 0.35
                    add_node(
                        node_id=target_profile['job_family'],
                        label=target_profile['job_family'],
                        node_type='job_family',
                        sample_count=target_profile['sample_count'],
                        top_skills=target_profile['required_skills'][:4],
                        top_cities=target_profile['top_cities'][:3],
                    )
                else:
                    overlap = 0.35
                    add_node(node_id=target, label=target, node_type='career_stage')
                edges.append(
                    JobGraphEdge(
                        source=profile['job_family'],
                        target=target,
                        edge_type='transfer',
                        weight=overlap,
                        reason='基于技能邻近性与岗位模板定义构建的可转岗路径。',
                    )
                )

        graph = JobGraph(
            nodes=nodes,
            edges=edges,
            metadata={
                'generated_at': datetime.now().isoformat(),
                'job_family_count': len(profiles),
                'node_count': len(nodes),
                'edge_count': len(edges),
            },
        )
        return graph.dict()

    def _build_report(
        self,
        raw_rows: list[dict],
        deduped_rows: list[dict],
        standardized_rows: list[dict],
        ignored_rows: list[dict],
        profiles: list[dict],
    ) -> dict:
        ignored_title_counter = Counter(row['job_title'] for row in ignored_rows if row['job_title'])
        family_counter = Counter(row['job_family'] for row in standardized_rows)
        return {
            'input_path': str(self.input_path),
            'generated_at': datetime.now().isoformat(),
            'raw_row_count': len(raw_rows),
            'deduped_row_count': len(deduped_rows),
            'standardized_row_count': len(standardized_rows),
            'ignored_row_count': len(ignored_rows),
            'job_family_distribution': dict(family_counter.most_common()),
            'ignored_title_distribution': dict(ignored_title_counter.most_common(20)),
            'generated_job_family_count': len(profiles),
        }

    def _write_outputs(self, standardized_rows: list[dict], profiles: list[dict], graph: dict, report: dict) -> None:
        standardized_path = self.output_dir / 'standardized_jobs.jsonl'
        with standardized_path.open('w', encoding='utf-8') as file_obj:
            for row in standardized_rows:
                file_obj.write(json.dumps(row, ensure_ascii=False) + '\n')

        for file_name, payload in {
            'job_profiles.json': profiles,
            'job_graph.json': graph,
            'build_report.json': report,
        }.items():
            path = self.output_dir / file_name
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description='Build knowledge base artifacts from raw job xls data.')
    parser.add_argument('--input', required=True, help='Path to the raw xls file.')
    parser.add_argument('--output-dir', default='data/knowledge_base', help='Directory to save artifacts.')
    args = parser.parse_args()

    builder = JobKnowledgeBuilder(input_path=args.input, output_dir=args.output_dir)
    report = builder.build()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
