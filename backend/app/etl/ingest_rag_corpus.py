import argparse
import json
from pathlib import Path

from backend.app.core.config import get_settings
from backend.app.repositories.rag_store import FileRagStore
from backend.app.schemas.rag import RagDocumentInput, RagDocumentMetadata
from backend.app.services.rag_chunker import RagChunker
from backend.app.services.rag_embedding import HashEmbeddingService


def load_documents(input_path: Path, default_source_type: str) -> list[RagDocumentInput]:
    if input_path.is_dir():
        documents: list[RagDocumentInput] = []
        for path in sorted(input_path.rglob('*')):
            if path.suffix.lower() not in {'.txt', '.md', '.json', '.jsonl'}:
                continue
            documents.extend(load_documents(path, default_source_type))
        return documents

    suffix = input_path.suffix.lower()
    if suffix in {'.txt', '.md'}:
        return [
            RagDocumentInput(
                document_id=input_path.stem,
                title=input_path.stem,
                text=input_path.read_text(encoding='utf-8'),
                metadata=RagDocumentMetadata(
                    source_type=default_source_type,
                    source_uri=str(input_path),
                    tags=[input_path.parent.name],
                ),
            )
        ]
    if suffix == '.json':
        payload = json.loads(input_path.read_text(encoding='utf-8'))
        if isinstance(payload, dict):
            payload = [payload]
        return [RagDocumentInput(**item) for item in payload]
    if suffix == '.jsonl':
        items = []
        for raw_line in input_path.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip()
            if not line:
                continue
            items.append(RagDocumentInput(**json.loads(line)))
        return items
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description='Ingest RAG corpus into the local store.')
    parser.add_argument('--input', required=True, help='Input file or directory containing txt/md/json/jsonl documents.')
    parser.add_argument('--store-dir', default='', help='Target RAG store directory.')
    parser.add_argument('--source-type', default='industry_report', help='Default source type for txt/md files.')
    parser.add_argument('--reset', action='store_true', help='Reset the existing store before ingesting.')
    args = parser.parse_args()

    settings = get_settings()
    store = FileRagStore(args.store_dir or settings.rag_store_dir)
    chunker = RagChunker(chunk_size=settings.rag_chunk_size, overlap=settings.rag_chunk_overlap)
    embedder = HashEmbeddingService()
    documents = load_documents(Path(args.input), args.source_type)
    response = store.upsert_documents(documents, chunker, embedder, reset_store=args.reset)
    print(json.dumps(response.dict(), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
