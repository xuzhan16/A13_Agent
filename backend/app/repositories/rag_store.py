import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from backend.app.schemas.rag import (
    RagChunkMetadata,
    RagChunkRecord,
    RagDocumentInput,
    RagIngestResponse,
    RagSearchFilters,
    RagStoreStats,
)


class FileRagStore:
    def __init__(self, store_dir: str) -> None:
        self.store_dir = Path(store_dir)
        self.documents_path = self.store_dir / 'documents.jsonl'
        self.chunks_path = self.store_dir / 'chunks.jsonl'
        self.manifest_path = self.store_dir / 'manifest.json'
        self._ensure_store()

    def upsert_documents(self, documents: list[RagDocumentInput], chunker: Any, embedder: Any, reset_store: bool = False) -> RagIngestResponse:
        existing_documents = {} if reset_store else {item.document_id: item for item in self.list_documents()}
        existing_chunks = [] if reset_store else self.list_chunks()
        remove_ids = {item.document_id for item in documents}
        retained_chunks = [item for item in existing_chunks if item.metadata.document_id not in remove_ids]
        skipped = 0
        new_chunks: list[RagChunkRecord] = []

        for document in documents:
            text = str(document.text or '').strip()
            if not text:
                skipped += 1
                continue
            existing_documents[document.document_id] = document
            for chunk_index, (chunk_text, char_start, char_end) in enumerate(chunker.chunk(text)):
                metadata = RagChunkMetadata(
                    document_id=document.document_id,
                    title=document.title,
                    chunk_id=f'{document.document_id}::chunk::{chunk_index}',
                    chunk_index=chunk_index,
                    locator=f'chunk {chunk_index + 1}',
                    char_start=char_start,
                    char_end=char_end,
                    **document.metadata.dict(),
                )
                new_chunks.append(
                    RagChunkRecord(
                        metadata=metadata,
                        text=chunk_text,
                        embedding=embedder.embed(chunk_text),
                        token_count=len(chunk_text),
                        keywords=embedder.extract_keywords(chunk_text, limit=12),
                    )
                )

        final_documents = list(existing_documents.values())
        final_chunks = retained_chunks + new_chunks
        updated_at = datetime.now(timezone.utc).isoformat()
        manifest = {
            'document_count': len(final_documents),
            'chunk_count': len(final_chunks),
            'updated_at': updated_at,
            'store_version': f'rag-store/{updated_at}',
        }
        self._write_jsonl(self.documents_path, final_documents)
        self._write_jsonl(self.chunks_path, final_chunks)
        self.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        return RagIngestResponse(
            ingested_documents=len(documents) - skipped,
            ingested_chunks=len(new_chunks),
            skipped_documents=skipped,
            store_version=manifest['store_version'],
        )

    def list_documents(self) -> list[RagDocumentInput]:
        return [RagDocumentInput(**payload) for payload in self._read_jsonl(self.documents_path)]

    def list_chunks(self, filters: Optional[RagSearchFilters] = None) -> list[RagChunkRecord]:
        chunks = [RagChunkRecord(**payload) for payload in self._read_jsonl(self.chunks_path)]
        if filters is None:
            return chunks
        return [item for item in chunks if self._match_filters(item, filters)]

    def get_stats(self) -> RagStoreStats:
        manifest = self._read_manifest()
        return RagStoreStats(
            document_count=int(manifest.get('document_count', 0)),
            chunk_count=int(manifest.get('chunk_count', 0)),
            store_version=str(manifest.get('store_version', 'rag-store/empty')),
            updated_at=str(manifest.get('updated_at', '')),
        )

    def _ensure_store(self) -> None:
        self.store_dir.mkdir(parents=True, exist_ok=True)
        if not self.documents_path.exists():
            self.documents_path.write_text('', encoding='utf-8')
        if not self.chunks_path.exists():
            self.chunks_path.write_text('', encoding='utf-8')
        if not self.manifest_path.exists():
            self.manifest_path.write_text(
                json.dumps(
                    {
                        'document_count': 0,
                        'chunk_count': 0,
                        'updated_at': '',
                        'store_version': 'rag-store/empty',
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding='utf-8',
            )

    def _read_manifest(self) -> dict[str, Any]:
        try:
            return json.loads(self.manifest_path.read_text(encoding='utf-8'))
        except Exception:
            return {
                'document_count': 0,
                'chunk_count': 0,
                'updated_at': '',
                'store_version': 'rag-store/empty',
            }

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        items: list[dict[str, Any]] = []
        for raw_line in path.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip()
            if not line:
                continue
            items.append(json.loads(line))
        return items

    @staticmethod
    def _write_jsonl(path: Path, items: list[Any]) -> None:
        lines = [json.dumps(item.dict() if hasattr(item, 'dict') else item, ensure_ascii=False) for item in items]
        payload = '\n'.join(lines)
        if payload:
            payload += '\n'
        path.write_text(payload, encoding='utf-8')

    @staticmethod
    def _match_filters(chunk: RagChunkRecord, filters: RagSearchFilters) -> bool:
        metadata = chunk.metadata
        if filters.source_types and metadata.source_type not in filters.source_types:
            return False
        if filters.document_ids and metadata.document_id not in filters.document_ids:
            return False
        if filters.job_families and not FileRagStore._match_term_group(filters.job_families, metadata.job_families, metadata):
            return False
        if filters.skills and not FileRagStore._match_term_group(filters.skills, metadata.skills, metadata):
            return False
        if filters.tags and not set(filters.tags).intersection(metadata.tags):
            return False
        return True

    @staticmethod
    def _match_term_group(request_terms: list[str], metadata_terms: list[str], metadata: RagChunkMetadata) -> bool:
        if set(request_terms).intersection(metadata_terms):
            return True
        haystack = ' '.join([metadata.title, metadata.document_id, metadata.source_uri, *metadata_terms, *metadata.tags]).lower()
        ascii_tokens: list[str] = []
        for term in request_terms:
            ascii_tokens.extend(re.findall(r'[a-z0-9_\+\#\./-]+', str(term).lower()))
        return bool(ascii_tokens) and any(token in haystack for token in ascii_tokens)
