# Career Planning Agent

面向“服务外包创新创业大赛”的大学生职业规划智能体项目。

当前版本已经完成从“规则型岗位匹配 Demo”到“证据驱动职业规划系统”的升级，核心能力覆盖：

- 简历上传、解析、结构化抽取与表单回填
- 学生画像生成与多轮追问
- 软素质显式评分
- 多维人岗匹配与证据链追溯
- 社会需求与行业发展趋势分析
- 职业路径推演与换岗路径分析
- Neo4j 知识图谱模式、个性化子图查询与可视化演示
- Markdown 职业报告导出

## 当前能力

- 岗位知识库构建：基于真实招聘 `xls` 数据生成岗位画像库、图谱和构建报告
- 学生画像抽取：支持 `txt / md / docx / pdf` 简历解析与结构化字段抽取
- 表单回填：自动回填姓名、学校、专业、技能、项目经历、实习经历、证书等字段
- 软素质建模：显式评估创新能力、沟通能力、抗压能力、学习能力、执行力
- 人岗匹配：按基础要求、职业技能、职业素养、发展潜力四维度打分
- 证据链追溯：支持从原始证据到指标、维度、总分的完整回溯
- 行业趋势分析：输出岗位冷热度、技能热度、行业变化和未来 3 年建议
- 图谱路径推演：支持岗位成长路径、转岗路径、个性化路径与个人子图查询
- 可视化演示：提供主 Demo 页面和 Neo4j 图谱演示页

## 项目结构

```text
backend/
  app/
    agents/
    api/
    core/
    etl/
    infra/
    prompts/
    repositories/
    schemas/
    services/
    static/
data/
  knowledge_base/
docs/
neo4j/
tests/
```

## 运行方式

### 1. 安装依赖

```bash
pip install -e .
```

### 2. 基于真实岗位数据构建知识库

```bash
python -m backend.app.etl.build_knowledge_base --input "D:/200-study/A13_Agent/20260226105856_457.xls" --output-dir "D:/200-study/A13_Agent/data/knowledge_base"
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`，常用配置如下：

```text
KNOWLEDGE_SOURCE=file
KNOWLEDGE_BASE_DIR=data/knowledge_base

ENABLE_LLM=false
LLM_API_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
LLM_TIMEOUT_SECONDS=30
```

说明：

- `KNOWLEDGE_SOURCE=file`：读取本地 `job_graph.json`
- `KNOWLEDGE_SOURCE=neo4j`：读取 Neo4j 图数据库
- 不配置 LLM 也可以完整演示，系统会自动走规则模式

### 4. 启动服务

```bash
uvicorn backend.app.main:app --reload
```

### 5. 打开页面

- 主 Demo 页面：[http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Neo4j 图谱演示页：[http://127.0.0.1:8000/neo4j-explorer](http://127.0.0.1:8000/neo4j-explorer)
- Swagger 文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 主 Demo 页面怎么玩

1. 点击“加载示例”，快速填充比赛演示数据
2. 或上传 `txt / md / docx / pdf` 简历，点击“解析文件”
3. 查看“结构化回填”区域，确认自动抽取结果
4. 点击“生成追问”，展示 Agent 的访谈与补全能力
5. 点击“生成职业报告”，展示画像、匹配、证据链、软素质、行业趋势和职业路径
6. 点击“查看我的图谱”，基于当前学生画像从全局图谱中实时查询个性化子图
7. 点击“导出 Markdown”，导出完整职业规划报告

## 个性化子图说明

主页面中的“查看我的图谱”不是新建一张独立图谱，而是基于当前学生画像结果，从全局岗位图谱中实时查询出一张个性化子图。

调用链路如下：

- 前端按钮触发 `POST /api/v1/planning/graph/personalized-subgraph`
- 后端读取当前学生的 `推荐岗位 / 已有技能 / 缺口技能 / 目标岗位`
- 通过 `KnowledgeRepository` 按当前配置路由到 `file` 或 `neo4j`
- 返回个性化子图 JSON
- 前端负责渲染岗位节点、技能节点、路径边和摘要信息

这样既避免前端直连 Neo4j，也方便做权限控制、结果加工和证据链展示。

## Neo4j 知识图谱模式

项目现已支持 `file` / `neo4j` 两种知识源。

### 一键启动 Neo4j

```bash
docker compose up -d neo4j neo4j-init
```

### 导入现有图谱到 Neo4j

```bash
python -m backend.app.etl.import_to_neo4j --drop-existing
```

### 切换系统到 Neo4j 模式

在 `.env` 中配置：

```text
KNOWLEDGE_SOURCE=neo4j
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
```

切换后能力包括：

- 多步路径查询
- 个性化路径过滤
- 个性化子图实时查询
- 边级证据链追溯
- Neo4j 图谱可视化演示

## 主要接口

### 基础能力

- `GET /api/v1/planning/job-families`
- `GET /api/v1/planning/job-graph`
- `POST /api/v1/planning/resume/parse`
- `POST /api/v1/planning/follow-up-questions`
- `POST /api/v1/planning/report`
- `POST /api/v1/planning/report/export-markdown`

### 图谱路径能力

- `POST /api/v1/planning/graph/transfer-paths`
- `POST /api/v1/planning/graph/personalized-paths`
- `POST /api/v1/planning/graph/path-evidence`
- `POST /api/v1/planning/graph/personalized-subgraph`

## 数据产物

当前用你的 `xls` 构建后得到：

- 原始数据：`9958`
- 去重后：`9178`
- 成功归并到 10 个核心岗位族：`3759`
- 已过滤非核心/低相关岗位：`5419`

生成产物位于 `data/knowledge_base/`：

- `standardized_jobs.jsonl`
- `job_profiles.json`
- `job_graph.json`
- `build_report.json`

## 当前推荐演示链路

### 方案一：主系统演示

1. 加载示例或上传简历
2. 展示结构化回填
3. 生成追问
4. 生成职业报告
5. 展示软素质评分、行业趋势、证据链和职业路径
6. 点击“查看我的图谱”，展示当前学生的推荐路径、缺口技能和证据来源

### 方案二：Neo4j 答辩演示

1. 打开 [Neo4j 图谱演示页](http://127.0.0.1:8000/neo4j-explorer)
2. 点击“加载学生 C 案例”
3. 点击“查询个性化路径”
4. 展示：
   - 最优路径摘要
   - 全部候选路径
   - 路径证据链
   - 图谱节点与关系详情

## 核心设计思路

- 离线构建岗位知识，不依赖在线即时推断
- 在线以 Agent 编排为主，保证稳定性和可解释性
- 匹配结果保留完整证据链，支持“为什么是 85 分”这类答辩问题
- 软素质和行业趋势单独显式建模，而不是隐含在长文本里
- 图谱层兼容 `file` 与 `neo4j`，便于比赛阶段稳态交付与后续升级

## 后续优化方向

### 业务效果

- 增加真实学生简历评测集，校验画像准确率和匹配准确率
- 引入岗位技能权重学习，减少模板型权重的主观性
- 继续细化行业趋势快照与薪资溢价分析

### Agent 能力

- 将追问从单轮问题生成升级为真正的多轮状态机
- 让 Agent 根据回答动态刷新画像、路径和报告
- 增加面试模拟、简历改写、岗位解释等子能力

### 前端展示

- 增加职业路径卡片和路径证据展开层
- 增加技能差距雷达图、行业趋势图表和答辩模式
- 增加 PDF 导出与打印样式

### 图谱与架构

- 扩展节点类型：岗位、技能、证书、行业、城市、课程
- 引入更多真实转岗案例和行业报告证据
- 做成“知识图谱 + 向量检索 + Agent”混合架构
