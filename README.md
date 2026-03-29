# Career Planning Agent

A FastAPI-based career planning system for university students. The project combines:

- structured resume parsing
- student profiling
- job matching with evidence trace
- career path planning
- industry trend analysis
- Neo4j knowledge graph queries
- optional LLM augmentation

The current runtime knowledge source is **Neo4j only**.

## Key Capabilities

- Build job requirement profiles from cleaned job data
- Build student profiles from resume text, projects, internships, campus activities, and follow-up answers
- Score student-job fit with explicit evidence chains
- Generate growth paths and transfer paths from Neo4j
- Render personalized subgraphs for the current student
- Surface industry trend analysis and missing-skill heat
- Export reports as Markdown

## Architecture

```text
FastAPI API
  -> CareerPlanningOrchestrator
  -> StudentProfiler / Matching / PathPlanner / ReportBuilder / IndustryTrend
  -> KnowledgeRepository (abstract contract)
  -> Neo4jKnowledgeRepository (runtime implementation)
  -> Neo4j
```

## Project Structure

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

## Quick Start

### 1. Install dependencies

```bash
pip install -e .
```

### 2. Build cleaned knowledge-base artifacts

```bash
python -m backend.app.etl.build_knowledge_base --input "<path-to-job-xls>" --output-dir "D:/200-study/A13_Agent/data/knowledge_base"
```

### 3. Start Neo4j

```bash
docker compose up -d neo4j neo4j-init
```

### 4. Import data into Neo4j

```bash
python -m backend.app.etl.import_to_neo4j --drop-existing
```

### 5. Configure `.env`

Copy `.env.example` to `.env` and fill in:

```text
APP_NAME=Career Planning Agent
APP_ENV=dev
APP_HOST=127.0.0.1
APP_PORT=8000
LOG_LEVEL=INFO
DEFAULT_TOP_K_MATCHES=3
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
ENABLE_LLM=false
LLM_API_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
LLM_TIMEOUT_SECONDS=30
```

Notes:
- Neo4j must be available before the app starts.
- When `ENABLE_LLM=false`, the system still works in rule-based mode.
- When `ENABLE_LLM=true`, LLM is used only as an enhancement layer, not the main scoring engine.

### 6. Start the app

```bash
uvicorn backend.app.main:app --reload
```

### 7. Open the demo

- Main demo: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Neo4j explorer: [http://127.0.0.1:8000/neo4j-explorer](http://127.0.0.1:8000/neo4j-explorer)
- Swagger docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Demo Flow

1. Upload or parse a resume
2. Review structured resume extraction and autofill results
3. Generate follow-up questions
4. Generate the career report
5. Inspect match evidence trace
6. Inspect soft-skill scoring and industry trend analysis
7. Switch from the global graph to the personalized subgraph
8. Export Markdown

## Neo4j Graph Model

The runtime graph contains:

- Node labels: `Job`, `Skill`, `Ability`, `City`, `Industry`
- Relationship types: `TRANSFER_TO`, `VERTICAL_TO`, `REQUIRES`, `DEPENDS_ON`, `LOCATED_IN`, `BELONGS_TO`, `RELATED_TO`

It supports:

- forward and reverse path search
- personalized transfer-path filtering by student skills
- related-job recommendation by skill overlap
- job clusters and influence ranking
- personalized subgraph retrieval for the current student

## Main APIs

### Planning APIs

- `GET /api/v1/planning/job-families`
- `GET /api/v1/planning/job-graph`
- `POST /api/v1/planning/resume/parse`
- `POST /api/v1/planning/follow-up-questions`
- `POST /api/v1/planning/report`
- `POST /api/v1/planning/report/export-markdown`

### Graph APIs

- `POST /api/v1/planning/graph/transfer-paths`
- `POST /api/v1/planning/graph/personalized-paths`
- `POST /api/v1/planning/graph/path-evidence`
- `POST /api/v1/planning/graph/personalized-subgraph`
- `POST /api/v1/planning/graph/related-jobs`
- `POST /api/v1/planning/graph/entry-points`
- `GET /api/v1/planning/graph/job-clusters`
- `GET /api/v1/planning/graph/job-influence`

## Testing

### Fast validation

```bash
python -m compileall backend tests
```

### Targeted tests

```bash
pytest tests/test_neo4j_repository.py tests/test_student_profiler_context.py -q
```

### Optional integration tests

The repository includes integration tests that expect a live Neo4j service. Enable them with:

```bash
set RUN_APP_INTEGRATION_TESTS=1
pytest -q
```

## Current Notes

- The runtime knowledge source is Neo4j only.
- `file_knowledge.py` and `in_memory_knowledge.py` have been removed.
- LLM extraction in `StudentProfilerService` is constrained by Neo4j vocabularies.
- `PathPlannerService` now uses Neo4j path queries and related-job recommendations.
- The main page can request and render a personalized graph subgraph.

## Recommended Next Steps

- Add richer evidence drill-down for soft-skill cards
- Add export for personalized graph images or PDF
- Add stronger evaluation datasets for resume structuring and matching calibration
- Optionally add MCP tools for LLM-initiated Neo4j lookups in a later stage
