from typing import Optional

from pydantic import BaseModel, Field


class RagDocumentMetadata(BaseModel):
    source_type: str = 'industry_report'
    source_uri: str = ''
    author: str = ''
    published_at: str = ''
    job_families: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    region: str = ''
    version: str = ''
    trust_score: float = 0.6
    extra: dict[str, str] = Field(default_factory=dict)


class RagDocumentInput(BaseModel):
    document_id: str
    title: str
    text: str
    metadata: RagDocumentMetadata = Field(default_factory=RagDocumentMetadata)


class RagChunkMetadata(RagDocumentMetadata):
    document_id: str
    title: str
    chunk_id: str
    chunk_index: int
    locator: str = ''
    char_start: int = 0
    char_end: int = 0


class RagChunkRecord(BaseModel):
    metadata: RagChunkMetadata
    text: str
    embedding: list[float] = Field(default_factory=list)
    token_count: int = 0
    keywords: list[str] = Field(default_factory=list)


class RagCitation(BaseModel):
    citation_id: str = ''
    document_id: str = ''
    chunk_id: str = ''
    title: str = ''
    source_type: str = ''
    source_uri: str = ''
    locator: str = ''
    published_at: str = ''
    excerpt: str = ''
    score: float = 0
    vector_score: float = 0
    lexical_score: float = 0
    rerank_score: float = 0
    matched_terms: list[str] = Field(default_factory=list)
    rationale: str = ''


class RagSearchFilters(BaseModel):
    source_types: list[str] = Field(default_factory=list)
    job_families: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: RagSearchFilters = Field(default_factory=RagSearchFilters)
    include_chunks: bool = True


class RagSearchResponse(BaseModel):
    query: str
    citations: list[RagCitation] = Field(default_factory=list)
    retrieval_plan: list[str] = Field(default_factory=list)
    total_hits: int = 0
    cache_hit: bool = False
    store_version: str = ''


class RagIngestRequest(BaseModel):
    documents: list[RagDocumentInput] = Field(default_factory=list)
    reset_store: bool = False


class RagIngestResponse(BaseModel):
    ingested_documents: int = 0
    ingested_chunks: int = 0
    skipped_documents: int = 0
    store_version: str = ''


class RagStoreStats(BaseModel):
    document_count: int = 0
    chunk_count: int = 0
    store_version: str = ''
    updated_at: str = ''


class RagEvidenceBundle(BaseModel):
    bundle_id: str
    topic: str
    query: str
    citations: list[RagCitation] = Field(default_factory=list)
    summary: str = ''
    retrieval_plan: list[str] = Field(default_factory=list)


class RagEvaluationSample(BaseModel):
    query: str
    relevant_document_ids: list[str] = Field(default_factory=list)
    filters: RagSearchFilters = Field(default_factory=RagSearchFilters)
    note: str = ''


class RagEvaluationRequest(BaseModel):
    samples: list[RagEvaluationSample] = Field(default_factory=list)
    top_k: int = 5


class RagEvaluationResult(BaseModel):
    query: str
    hit_at_k: float = 0
    mrr: float = 0
    matched_document_ids: list[str] = Field(default_factory=list)
    top_citations: list[RagCitation] = Field(default_factory=list)


class RagEvaluationSummary(BaseModel):
    top_k: int = 5
    sample_count: int = 0
    mean_hit_at_k: float = 0
    mean_mrr: float = 0
    results: list[RagEvaluationResult] = Field(default_factory=list)
