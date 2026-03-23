from dataclasses import dataclass


@dataclass(frozen=True)
class JobFamilyTemplate:
    job_family: str
    aliases: tuple[str, ...]
    description: str
    preferred_majors: tuple[str, ...]
    required_skills: tuple[str, ...]
    bonus_skills: tuple[str, ...]
    soft_skills: tuple[str, ...]
    certificates: tuple[str, ...]
    practice_requirements: tuple[str, ...]
    vertical_growth_path: tuple[str, ...]
    transfer_paths: tuple[str, ...]


JOB_FAMILY_TEMPLATES: tuple[JobFamilyTemplate, ...] = (
    JobFamilyTemplate(
        job_family='Java开发工程师',
        aliases=('java', 'java开发', '后端开发', '后端工程师'),
        description='负责后端业务开发、接口设计、数据库建模与系统稳定性优化。',
        preferred_majors=('计算机', '软件工程', '信息工程'),
        required_skills=('Java', 'Spring Boot', 'MySQL', '接口设计', '数据结构'),
        bonus_skills=('Redis', '消息队列', 'Linux', '微服务', 'SQL'),
        soft_skills=('学习能力', '沟通能力', '抗压能力', '团队协作'),
        certificates=('软考中级', '英语四级'),
        practice_requirements=('至少1段项目经历', '有后端开发作品'),
        vertical_growth_path=('Java开发工程师', '高级开发工程师', '技术负责人', '架构师'),
        transfer_paths=('前端开发工程师', '软件测试工程师', '实施工程师'),
    ),
    JobFamilyTemplate(
        job_family='前端开发工程师',
        aliases=('前端开发', '前端工程师', 'web前端', 'frontend'),
        description='负责 Web 页面开发、交互实现、性能优化与前后端协作。',
        preferred_majors=('计算机', '软件工程', '数字媒体技术'),
        required_skills=('HTML', 'CSS', 'JavaScript', 'Vue', '前端工程化'),
        bonus_skills=('React', 'TypeScript', '可视化', '性能优化', 'Webpack'),
        soft_skills=('审美表达', '沟通能力', '学习能力', '团队协作'),
        certificates=('英语四级',),
        practice_requirements=('至少1个前端项目', '能展示页面作品'),
        vertical_growth_path=('前端开发工程师', '高级前端工程师', '前端负责人', '体验技术专家'),
        transfer_paths=('产品专员', 'Java开发工程师', '软件测试工程师'),
    ),
    JobFamilyTemplate(
        job_family='C/C++嵌入式工程师',
        aliases=('c/c++', 'c++', '嵌入式', '嵌入式开发', 'c语言'),
        description='负责嵌入式系统开发、驱动适配、协议栈调试与性能优化。',
        preferred_majors=('计算机', '通信工程', '电子信息', '自动化'),
        required_skills=('C语言', 'C++', '嵌入式开发', '数据结构', '调试能力'),
        bonus_skills=('Linux', 'AUTOSAR', 'CAN', '汇编', '驱动开发'),
        soft_skills=('问题定位能力', '抗压能力', '学习能力', '团队协作'),
        certificates=('英语四级',),
        practice_requirements=('有硬件或嵌入式项目', '具备调试经验'),
        vertical_growth_path=('C/C++嵌入式工程师', '高级嵌入式工程师', '平台负责人', '技术专家'),
        transfer_paths=('硬件测试工程师', '技术支持工程师', '项目经理'),
    ),
    JobFamilyTemplate(
        job_family='软件测试工程师',
        aliases=('软件测试', '测试工程师', '质量管理/测试', '测试开发'),
        description='负责测试方案设计、功能测试、缺陷跟踪与质量保障。',
        preferred_majors=('计算机', '软件工程', '信息管理'),
        required_skills=('测试用例设计', '缺陷管理', '接口测试', 'SQL', '质量意识'),
        bonus_skills=('Python', '自动化测试', '性能测试', 'Linux', 'Postman'),
        soft_skills=('细致严谨', '沟通能力', '抗压能力', '执行力'),
        certificates=('ISTQB', '英语四级'),
        practice_requirements=('有测试项目经验', '熟悉至少一种测试工具'),
        vertical_growth_path=('软件测试工程师', '高级测试工程师', '测试负责人', '质量经理'),
        transfer_paths=('实施工程师', 'Java开发工程师', '技术支持工程师'),
    ),
    JobFamilyTemplate(
        job_family='硬件测试工程师',
        aliases=('硬件测试', '硬件测试工程师'),
        description='负责硬件产品功能、性能、稳定性测试以及问题复现与定位。',
        preferred_majors=('电子信息', '自动化', '通信工程', '计算机'),
        required_skills=('硬件测试', '仪器使用', '问题定位', '测试记录', '基础电路'),
        bonus_skills=('物联网', '嵌入式调试', '售后支持', '脚本能力', '示波器'),
        soft_skills=('动手能力', '学习能力', '责任心', '沟通能力'),
        certificates=('英语四级',),
        practice_requirements=('有实验室或测试经历', '有硬件相关课程基础'),
        vertical_growth_path=('硬件测试工程师', '高级硬件测试工程师', '测试负责人', '质量经理'),
        transfer_paths=('C/C++嵌入式工程师', '技术支持工程师', '实施工程师'),
    ),
    JobFamilyTemplate(
        job_family='实施工程师',
        aliases=('实施工程师', '实施顾问'),
        description='负责软件部署、培训、客户现场支持、数据处理与项目交付。',
        preferred_majors=('计算机', '信息管理', '地理信息', '测绘工程'),
        required_skills=('系统部署', '数据库基础', '客户沟通', '文档编写', '现场支持'),
        bonus_skills=('Oracle', 'MySQL', 'ArcGIS', '需求理解', '数据处理'),
        soft_skills=('沟通能力', '责任心', '抗压能力', '学习能力'),
        certificates=('英语四级',),
        practice_requirements=('接受出差', '有客户沟通或驻场经历'),
        vertical_growth_path=('实施工程师', '高级实施工程师', '项目经理', '交付负责人'),
        transfer_paths=('技术支持工程师', '项目经理', '软件测试工程师'),
    ),
    JobFamilyTemplate(
        job_family='技术支持工程师',
        aliases=('技术支持工程师', '技术支持', '售后技术支持'),
        description='负责产品问题排查、客户支持、售后服务与问题闭环。',
        preferred_majors=('计算机', '电子信息', '网络工程'),
        required_skills=('问题排查', '客户沟通', '基础网络', '文档记录', '服务意识'),
        bonus_skills=('Linux', '数据库基础', '脚本能力', '产品理解', '网络排障'),
        soft_skills=('耐心', '沟通能力', '责任心', '抗压能力'),
        certificates=('英语四级',),
        practice_requirements=('有售后或答疑经历', '能够快速定位问题'),
        vertical_growth_path=('技术支持工程师', '高级支持工程师', '支持主管', '客户成功负责人'),
        transfer_paths=('实施工程师', '项目经理', '销售工程师'),
    ),
    JobFamilyTemplate(
        job_family='产品专员',
        aliases=('产品专员/助理', '产品专员', '产品助理'),
        description='负责需求整理、竞品分析、文档输出与跨团队协作推进。',
        preferred_majors=('计算机', '工业工程', '管理科学', '设计学'),
        required_skills=('需求分析', '原型设计', '文档能力', '沟通协调', '逻辑思维'),
        bonus_skills=('Axure', 'Figma', '数据分析', '竞品分析', '流程设计'),
        soft_skills=('沟通能力', '同理心', '学习能力', '推动力'),
        certificates=('英语四级',),
        practice_requirements=('有校园产品或项目策划经历', '能展示文档或原型'),
        vertical_growth_path=('产品专员', '产品经理', '高级产品经理', '产品负责人'),
        transfer_paths=('项目经理', '前端开发工程师', '销售工程师'),
    ),
    JobFamilyTemplate(
        job_family='项目经理',
        aliases=('项目经理/主管', '项目经理', '项目专员/助理'),
        description='负责项目计划、资源协调、风险控制、交付推进与客户对接。',
        preferred_majors=('计算机', '信息管理', '工业工程', '管理学'),
        required_skills=('项目管理', '沟通协调', '进度控制', '风险管理', '文档汇报'),
        bonus_skills=('敏捷开发', '需求管理', '实施交付', '跨部门协作', 'Jira'),
        soft_skills=('领导力', '抗压能力', '责任心', '沟通能力'),
        certificates=('PMP', '英语四级'),
        practice_requirements=('有团队协作或项目负责经历', '具备推进意识'),
        vertical_growth_path=('项目经理', '高级项目经理', '交付总监', '业务负责人'),
        transfer_paths=('实施工程师', '技术支持工程师', '产品专员'),
    ),
    JobFamilyTemplate(
        job_family='销售工程师',
        aliases=('销售工程师', '售前工程师', '解决方案工程师'),
        description='负责技术方案讲解、客户需求洞察、售前支持与商务推进。',
        preferred_majors=('计算机', '电子信息', '市场营销', '工商管理'),
        required_skills=('方案表达', '客户沟通', '需求理解', '演示能力', '商务协同'),
        bonus_skills=('行业理解', '招投标', '演示文档', '产品知识', '方案设计'),
        soft_skills=('沟通能力', '抗压能力', '应变能力', '学习能力'),
        certificates=('英语四级',),
        practice_requirements=('有演讲或商务拓展经历', '愿意面向客户'),
        vertical_growth_path=('销售工程师', '高级销售工程师', '解决方案经理', '区域负责人'),
        transfer_paths=('技术支持工程师', '产品专员', '项目经理'),
    ),
)


JOB_FAMILY_BY_NAME = {item.job_family: item for item in JOB_FAMILY_TEMPLATES}
