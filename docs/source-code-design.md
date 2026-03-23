# 源码设计说明

## 1. 设计目标

这个项目不是普通问答机器人，而是“证据驱动的闭环职业规划 Agent”。

源码设计必须同时满足：

- 业务上可解释
- 工程上可扩展
- 比赛展示时有 Agent 感
- 后续容易接真实数据和真实大模型

## 2. 总体设计

### 2.1 分层

- `API 层`：负责请求接入、协议校验、响应输出
- `Agent 编排层`：负责串起完整规划流程
- `领域服务层`：负责学生画像、岗位画像、匹配、路径规划、报告生成、追问生成、简历解析
- `知识仓储层`：负责岗位知识、图谱关系、技能词典
- `ETL 层`：负责原始 `xls` 清洗、岗位标准化、画像与图谱构建
- `静态前端层`：负责比赛演示页、图谱展示、报告预览与导出
- `基础设施层`：负责可插拔 LLM、后续向量库、数据库、文件解析器

### 2.2 当前主链路

1. `etl/build_knowledge_base.py` 从原始 `xls` 构建知识库产物
2. `FileKnowledgeRepository` 读取岗位画像和图谱
3. `ResumeParserService` 解析学生简历文件
4. `StudentProfilerService` 进行规则抽取或 LLM 增强
5. `JobProfilerService` 召回候选岗位族
6. `MatchingService` 完成多维人岗匹配
7. `FollowUpQuestionService` 生成高价值追问
8. `PathPlannerService` 生成主路径、备选路径、换岗路径
9. `ReportBuilderService` 生成报告并按配置增强
10. `CareerPlanningOrchestrator` 统一输出
11. `static/` 前端页面完成可视化展示和导出

## 3. 第四阶段新增内容

### 3.1 前端 Demo

- 新增 `backend/app/static/index.html`
- 新增 `backend/app/static/styles.css`
- 新增 `backend/app/static/app.js`
- 使用 FastAPI 直接挂载静态资源，无需单独前端构建链

### 3.2 图谱展示

- 读取 `/api/v1/planning/job-graph`
- 在前端用 SVG 进行轻量可视化
- 同时展示纵向岗位路径和换岗路径

### 3.3 报告导出

- 新增 `/api/v1/planning/report/export-markdown`
- 支持从前端直接下载 Markdown 职业规划报告

## 4. 为什么当前不强制使用 Neo4j

当前岗位图谱规模有限，且核心目标是“解释清楚”和“展示稳定”，不是复杂图查询。
因此当前阶段使用 `JSON 图谱 + API + 前端可视化` 是更优工程取舍。

如果后续要做：

- 更大规模岗位生态
- 技能节点、课程节点、证书节点等多类型图谱
- 多跳路径推理
- 图算法分析
- 图数据库运营能力

再引入 Neo4j 会更合理，而且与当前结构天然兼容。

## 5. 当前状态

- 后端主链路可运行
- 真实岗位知识库可构建
- 图谱可通过 API 输出
- 简历解析可用
- 追问生成可用
- 报告生成可用
- Demo 页面可直接演示
