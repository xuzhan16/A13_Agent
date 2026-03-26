# Source Code Design

## 1. Goals

This project is not a generic chatbot. It is an evidence-driven career planning agent.

The source code design optimizes for four goals:

- Explainability: every profile, score, path, and suggestion can be traced back to evidence.
- Extensibility: rules, LLM augmentation, graph logic, and frontend visualization can evolve independently.
- Demo readiness: the system must work in competition demos and answer "why" questions from judges.
- Upgrade path: the project must support a smooth migration from local JSON graph data to Neo4j.

## 2. Overall Architecture

### 2.1 Layers

- API layer: request handling, validation, response models.
- Agent orchestration layer: end-to-end workflow coordination.
- Domain service layer: student profiling, matching, path planning, report generation, follow-up questions, resume parsing, soft-skill scoring, industry trend analysis.
- Knowledge repository layer: job profiles, graph data, skill lexicons, and graph database access.
- ETL layer: raw xls cleaning, job normalization, graph construction, Neo4j import.
- Static frontend layer: demo UI, evidence view, graph view, report preview, export.
- Infrastructure layer: pluggable LLM client, file parsers, config, and future database/vector extensions.

### 2.2 Main Runtime Flow

1. `etl/build_knowledge_base.py` builds local knowledge artifacts from raw xls data.
2. `KnowledgeRepository` selects `FileKnowledgeRepository` or `Neo4jKnowledgeRepository` from config.
3. `ResumeParserService` extracts resume text.
4. `ResumeStructuringService` produces structured fields and form-fill suggestions.
5. `StudentProfilerService` builds the student profile and evidence pool.
6. `SoftSkillAssessmentService` scores explicit soft-skill dimensions.
7. `JobProfilerService` recalls candidate job families.
8. `MatchingService` computes match scores and evidence traces.
9. `PathPlannerService` builds main paths, fallback paths, and transfer paths.
10. `IndustryTrendService` generates role heat, skill heat, and trend insights.
11. `ReportBuilderService` assembles the career report and optional LLM enhancement.
12. `FollowUpQuestionService` generates high-value follow-up questions.
13. `KnowledgeRepository.get_personalized_subgraph()` queries a personalized subgraph for the current student.
14. `CareerPlanningOrchestrator` returns the final response payload.
15. The static frontend renders all views, including global graph and personalized graph modes.

## 3. Core Modules

### 3.1 API Layer

The current API surface has four groups:

- Planning APIs: job families, job graph, resume parsing, follow-up generation, report generation, markdown export.
- Graph path APIs: transfer path query, personalized path query, path evidence query.
- Personalized subgraph API: query a graph slice for the current student.
- Health APIs: service status checks.

The API layer only coordinates protocol concerns and never owns business scoring logic.

### 3.2 Agent Orchestration Layer

`CareerPlanningOrchestrator` is the top-level runtime entry point.

It is responsible for:

- invoking student profiling,
- invoking job recall and matching,
- invoking path planning,
- invoking report generation,
- invoking follow-up generation,
- aggregating metadata such as profile mode, report mode, knowledge source, and LLM flags.

This keeps the outer interface stable while allowing the internals to evolve.

### 3.3 Student Profiling Pipeline

The student profiling pipeline includes:

- `ResumeParserService`: parses `txt / md / docx / pdf` files.
- `ResumeStructuringService`: extracts structured fields, matches skills, flags pending fields, and produces form-fill suggestions.
- `StudentProfilerService`: builds the normalized student profile, including:
  - basic info,
  - career preferences,
  - hard skills,
  - soft skills,
  - certificates,
  - strengths and gaps,
  - completeness and competitiveness,
  - raw evidence pool.

The implementation remains rule-first with optional LLM augmentation.

### 3.4 Explicit Soft-Skill Scoring

`SoftSkillAssessmentService` makes soft skills explicit instead of hiding them in project text.

Current soft-skill dimensions:

- innovation,
- communication,
- stress tolerance,
- learning agility,
- execution.

Each output includes:

- score,
- level,
- indicator breakdown,
- evidence references,
- improvement suggestions.

These results are written into both student profile and report output.

### 3.5 Matching and Evidence Trace

`MatchingService` compares student profile and job profile and returns:

- overall score,
- match summary,
- matched skills,
- missing skills,
- four scoring dimensions:
  - basic requirements,
  - professional skills,
  - professional literacy,
  - development potential,
- `evidence_trace`.

The evidence trace is layered from raw evidence to indicator scores, dimension scores, and final score.

This supports judge questions such as "Why is this 85 instead of 78 or 92?"

### 3.6 Path Planning

`PathPlannerService` has shifted from template-first logic to graph-first logic.

Current output categories:

- main path: the best-fit long-term path from the top matched role.
- fallback path: a safer route based on the second-best role.
- transfer path: a flexible route based on adjacent skills and graph relations.

Each path now carries:

- `path_jobs`,
- `target_role`,
- `readiness_score`,
- `estimated_success_rate`,
- `estimated_time_cost`,
- `missing_skills`,
- `evidence_sources`.

Each step also contains edge-level fields such as success rate, time cost, required skills, missing skills, and evidence.

### 3.7 Industry Trend Analysis

`IndustryTrendService` adds the "social demand and industry trend" section to the report.

Current outputs include:

- job heat analysis,
- missing-skill heat analysis,
- industry shift themes,
- personalized three-year advice.

This module is linked to the current recommended jobs and missing skills instead of producing generic text.

### 3.8 Report Generation

`ReportBuilderService` assembles all intermediate outputs into the final career report.

Current report sections include:

- executive summary,
- student profile overview,
- explicit soft-skill profile,
- recommended roles,
- career path suggestions,
- industry trend analysis,
- action plan.

When LLM is enabled, it only enhances expression and does not change the factual structure.

## 4. Repository Layer

### 4.1 Abstract Repository Contract

`KnowledgeRepository` is the core abstraction layer.

It defines:

- job profile reads,
- skill lexicon reads,
- graph reads,
- path queries,
- personalized path queries,
- path evidence queries,
- personalized subgraph queries.

Upper layers do not need to care whether the backing source is JSON or Neo4j.

### 4.2 FileKnowledgeRepository

The file repository reads:

- `job_profiles.json`,
- `job_graph.json`.

It is suitable for:

- stable local demos,
- offline operation,
- environments without graph database dependencies.

### 4.3 Neo4jKnowledgeRepository

The Neo4j repository supports:

- loading the full job graph,
- querying all paths from role A to role B,
- querying personalized paths by student skills,
- loading full evidence for any path.

Compared with static JSON, Neo4j is better for questions such as:

- why Java developer can move toward architect,
- which path is feasible for this student now,
- which skills must be added step by step,
- which graph slice should be shown to this specific student.

### 4.4 Personalized Subgraph Aggregation

The repository abstraction now exposes `get_personalized_subgraph()`.

This method does not create a new global graph. It extracts a student-specific graph slice from the existing knowledge graph.

Current inputs:

- `focus_job`,
- `target_job`,
- `recommended_jobs`,
- `student_skills`,
- `missing_skills`.

Current outputs:

- personalized job nodes,
- owned skill nodes,
- missing skill nodes,
- selected path edges and candidate path edges,
- a `summary` object containing:
  - focus job,
  - target job,
  - recommended jobs,
  - owned skills,
  - missing skills,
  - selected path,
  - readiness score,
  - success rate,
  - time cost,
  - evidence sources.

This allows the frontend to render "View My Graph" without exposing Neo4j to the browser.

### 4.5 Config-Based Switching

`dependencies.py` switches repository implementation by `KNOWLEDGE_SOURCE`:

- `file`,
- `neo4j`.

This preserves backward compatibility for upper layers.

## 5. ETL and Knowledge Construction

### 5.1 Local Knowledge Base Construction

`etl/build_knowledge_base.py` is responsible for:

- raw job data cleaning,
- job normalization,
- job profile construction,
- graph edge construction,
- build report generation.

Artifacts:

- `standardized_jobs.jsonl`,
- `job_profiles.json`,
- `job_graph.json`,
- `build_report.json`.

### 5.2 Neo4j Import

`etl/import_to_neo4j.py` imports local graph and job profiles into Neo4j.

Imported graph content includes:

- `Job` nodes,
- `Skill` nodes,
- `Ability` nodes,
- `TRANSFER_TO` relations,
- `VERTICAL_TO` relations,
- `REQUIRES` relations,
- `DEPENDS_ON` relations.

Supporting files include:

- `neo4j/init.cypher`,
- `neo4j/query_examples.cypher`,
- `docker-compose.yml`.

## 6. Frontend Design

### 6.1 Main Demo Page

Main page files:

- `static/index.html`,
- `static/app.js`,
- `static/styles.css`.

Current responsibilities:

- resume upload and parsing,
- structured backfill preview,
- follow-up view,
- match result view,
- evidence trace view,
- soft-skill view,
- industry trend view,
- personalized graph button and summary view,
- global graph / personalized graph mode switching,
- report preview and export.

The runtime flow for "View My Graph" is:

1. The user generates a career report first.
2. The frontend extracts current focus role, recommended roles, target role, owned skills, and missing skills from the latest response.
3. The frontend calls `POST /api/v1/planning/graph/personalized-subgraph`.
4. The backend uses the active `KnowledgeRepository` implementation to query the graph slice.
5. The frontend renders job nodes, skill nodes, path edges, and summary cards.

This design avoids direct browser-to-Neo4j access and keeps security and result shaping inside FastAPI.

### 6.2 Neo4j Explorer Page

Dedicated graph explorer files:

- `static/neo4j-explorer.html`,
- `static/neo4j-explorer.js`.

Current responsibilities:

- Neovis.js graph visualization,
- node detail view,
- relation detail view,
- multi-step path query,
- personalized path query,
- path evidence view,
- fixed student-C demo scenario: Java developer to architect.

This page is mainly for graph-focused defense demos.

## 7. Why the System Uses Dual Graph Modes

The current system is no longer JSON-only. It uses two graph modes:

- JSON graph: stable delivery and quick local demo.
- Neo4j graph: complex path query and stronger evidence traversal.

Why this matters:

- competition demos need stability,
- defense sessions need deeper explanation,
- the engineering design needs a future upgrade path.

The architecture does not reject Neo4j. It makes Neo4j an optional enhancement mode.

## 8. Testing and Validation

Current validation methods include:

- `compileall` static compilation checks,
- frontend script syntax checks,
- `TestClient` smoke tests,
- targeted repository and path-planning tests.

Current focus areas include:

- resume parsing,
- structured backfill,
- report generation,
- evidence trace payloads,
- graph path queries,
- personalized subgraph query inputs and outputs,
- Neo4j repository mapping logic.

## 9. Current Status

The current system already supports:

- runnable backend main flow,
- real job knowledge base construction,
- resume parsing and structured backfill,
- explicit soft-skill scoring,
- matching with evidence trace,
- industry trend analysis,
- main demo page workflow,
- switchable Neo4j graph mode,
- graph path and path evidence APIs,
- main-page personalized subgraph view.

## 10. Future Evolution

- Upgrade industry trend data from static snapshots to scheduled pipelines.
- Upgrade follow-up generation into a true multi-turn state machine.
- Tighten the linkage between path planning and evidence trace on the main page.
- Extend graph node types to certificates, courses, industries, and cities.
- Move toward a hybrid architecture of knowledge graph plus retrieval plus agent orchestration.
