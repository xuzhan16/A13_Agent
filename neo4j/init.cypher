CREATE CONSTRAINT job_name_unique IF NOT EXISTS
FOR (j:Job)
REQUIRE j.name IS UNIQUE;

CREATE CONSTRAINT skill_name_unique IF NOT EXISTS
FOR (s:Skill)
REQUIRE s.name IS UNIQUE;

CREATE CONSTRAINT ability_name_unique IF NOT EXISTS
FOR (a:Ability)
REQUIRE a.name IS UNIQUE;

CREATE INDEX job_name_idx IF NOT EXISTS
FOR (j:Job)
ON (j.name);

CREATE INDEX skill_name_idx IF NOT EXISTS
FOR (s:Skill)
ON (s.name);

CREATE INDEX ability_name_idx IF NOT EXISTS
FOR (a:Ability)
ON (a.name);

CREATE INDEX transfer_success_rate_idx IF NOT EXISTS
FOR ()-[r:TRANSFER_TO]-()
ON (r.success_rate);

MERGE (java:Job {name: 'Java开发工程师'})
SET java.label = 'Java开发工程师',
    java.node_type = 'job_family',
    java.description = '负责后端业务开发、接口设计、数据库建模与系统稳定性优化。',
    java.sample_count = 537,
    java.top_skills = ['Java', 'Spring Boot', 'MySQL', '接口设计'],
    java.top_cities = ['深圳', '武汉', '南京'];

MERGE (senior:Job {name: '高级开发工程师'})
SET senior.label = '高级开发工程师',
    senior.node_type = 'career_stage',
    senior.description = '承担核心模块设计、性能优化和复杂问题攻坚。';

MERGE (architect:Job {name: '架构师'})
SET architect.label = '架构师',
    architect.node_type = 'career_stage',
    architect.description = '负责系统抽象、技术路线设计和跨团队架构治理。';

MERGE (sys:Skill {name: '系统设计'})
SET sys.category = 'architecture',
    sys.difficulty = 'hard',
    sys.market_demand = 0.92,
    sys.trend = 'growing';

MERGE (micro:Skill {name: '微服务'})
SET micro.category = 'backend',
    micro.difficulty = 'medium',
    micro.market_demand = 0.88,
    micro.trend = 'stable';

MERGE (dist:Skill {name: '分布式架构'})
SET dist.category = 'architecture',
    dist.difficulty = 'hard',
    dist.market_demand = 0.95,
    dist.trend = 'growing';

MERGE (communication:Ability {name: '沟通能力'})
SET communication.level = 'senior',
    communication.description = '能够完成跨团队技术沟通、方案评审和技术推动。';

MERGE (java)-[:REQUIRES {requirement_type: 'required', importance: 1.0}]->(micro)
MERGE (senior)-[:REQUIRES {requirement_type: 'required', importance: 1.0}]->(sys)
MERGE (architect)-[:REQUIRES {requirement_type: 'required', importance: 1.0}]->(dist)
MERGE (architect)-[:DEPENDS_ON {dependency_strength: 0.9}]->(communication)

MERGE (java)-[r1:VERTICAL_TO]->(senior)
SET r1.success_rate = 0.86,
    r1.time_cost = '1-2年',
    r1.difficulty = 'medium',
    r1.required_skills = ['微服务', '系统设计', '性能优化'],
    r1.evidence = ['catalog.vertical_growth_path', '后端工程经验积累规律'],
    r1.case_count = 58,
    r1.weight = 0.92,
    r1.reason = '基于岗位标准晋升路径与后端能力演进逻辑。';

MERGE (senior)-[r2:VERTICAL_TO]->(architect)
SET r2.success_rate = 0.71,
    r2.time_cost = '2-3年',
    r2.difficulty = 'high',
    r2.required_skills = ['分布式架构', '架构思维', '业务抽象'],
    r2.evidence = ['行业报告', '真实技术晋升案例'],
    r2.case_count = 24,
    r2.weight = 0.84,
    r2.reason = '需要完成从核心模块设计到整体架构设计的能力跃迁。';
