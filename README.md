# Career Planning Agent

面向“服务外包创新创业大赛”的大学生职业规划智能体项目。

当前版本已经完成四个阶段：

- 第一阶段：后端主链路与 Agent 编排骨架
- 第二阶段：真实 `xls` 数据清洗、岗位画像库与岗位图谱构建
- 第三阶段：简历解析、多轮追问、可插拔 LLM 增强
- 第四阶段：前端 Demo 页面、图谱可视化、报告导出、完整演示链路

## 当前能力

- 岗位知识库构建
- 学生画像抽取与增强
- 多维人岗匹配
- 职业路径与换岗路径展示
- 多轮追问生成
- 职业报告生成与 Markdown 导出
- Demo 页面可直接演示整条业务链路

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
tests/
```

## 如何跑通

### 1. 安装依赖

```bash
pip install -e .
```

### 2. 基于真实岗位数据构建知识库

```bash
python -m backend.app.etl.build_knowledge_base --input "C:/Users/15723/Downloads/20260226105856_457 (1).xls" --output-dir "D:/200-study/A13_Agent/data/knowledge_base"
```

### 3. 可选：配置 LLM 增强

复制 `.env.example` 为 `.env`，按需填写：

```text
ENABLE_LLM=true
LLM_API_BASE_URL=https://your-openai-compatible-endpoint/v1
LLM_API_KEY=your_key
LLM_MODEL=your_model
LLM_TIMEOUT_SECONDS=30
KNOWLEDGE_BASE_DIR=data/knowledge_base
```

如果不配置，系统会自动以规则模式运行，仍然可以完整演示。

### 4. 启动服务

```bash
uvicorn backend.app.main:app --reload
```

### 5. 打开页面

- Demo 页面：[http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Swagger 文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Demo 页面怎么玩

1. 点击“加载示例”，快速填充比赛演示数据
2. 或者先上传 `txt/md/docx` 简历，点击“解析文件”
3. 点击“生成追问”，展示 Agent 的访谈能力
4. 点击“生成职业报告”，展示画像、匹配、图谱和报告
5. 点击“导出 Markdown”或“导出 JSON”保存结果

## 主要接口

- `GET /api/v1/planning/job-families`
- `GET /api/v1/planning/job-graph`
- `POST /api/v1/planning/resume/parse`
- `POST /api/v1/planning/follow-up-questions`
- `POST /api/v1/planning/report`
- `POST /api/v1/planning/report/export-markdown`

## 真实数据构建结果

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

## 后续优化点

### 业务效果优化

- 增加真实学生简历评测集，校验画像准确率和匹配准确率
- 引入岗位技能权重学习，减少当前模板型权重的主观性
- 让行动计划更贴近不同岗位的真实求职节奏
- 为报告增加“证据引用段落”，提升答辩说服力

### Agent 能力优化

- 将追问从单轮问题生成升级为真正的多轮状态机
- 让 Agent 根据回答动态刷新画像和推荐岗位
- 增加面试模拟、简历改写、岗位解释等子能力

### 前端展示优化

- 增加岗位画像详情抽屉和技能差距雷达图
- 增加一键切换“示例学生案例”
- 增加 PPT 风格的答辩演示模式
- 增加 PDF 导出与打印样式

### 架构与知识图谱优化

- 当前图谱用 `job_graph.json + API` 即可满足比赛演示和当前规模需求
- 后续完全可以升级为“知识图谱”方案

可行升级路线：

1. 继续沿用当前 JSON 图谱结构，先增加更多节点类型：岗位、技能、证书、行业、城市、课程
2. 将图谱存储切换到 Neo4j 或图数据库，支持复杂多跳查询
3. 增加图谱构建规则与图算法，如技能相似度、路径推荐、中心性分析
4. 做成“图谱 + 向量检索 + Agent”混合架构，提升解释性与检索能力

换句话说，**知识图谱后续优化完全可以加进去，而且是很自然的升级方向**。只是以你当前比赛阶段看，先用轻量 JSON 图谱更稳、更容易交付。
