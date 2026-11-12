"""Reuse current saved summaries or sample source sections for whole-paper questions."""

import json
import re

from backend.services.document_processor.chunk_models import DocumentChunk
from backend.services.rag_service.models import RagNotReady, RetrievalHit, RetrievalScope
from backend.services.summary_service.models import TEXT_FIELDS, SummaryError
from backend.services.summary_service.storage import SummaryNotReady, read_summary
from backend.shared.config import Settings
from pymongo.database import Database


def section_samples(chunks: list[DocumentChunk], limit: int = 20) -> list[DocumentChunk]:
    groups: dict[tuple, list[DocumentChunk]] = {}
    for chunk in sorted(chunks, key=lambda item: item.chunk_index):
        key = tuple(sorted(chunk.heading_path.items())) or (("page", str(chunk.page_number)),)
        groups.setdefault(key, []).append(chunk)
    # Keep bibliography/acknowledgements behind scientific sections.
    ordered = sorted(
        groups.items(),
        key=lambda item: bool(re.search(r"references|bibliography|acknowledg", str(item[0]), re.I)),
    )
    representatives = [
        next((chunk for chunk in group if len(chunk.content) >= 150), group[0])
        for _, group in ordered
    ]
    if not chunks:
        return []
    scientific = [
        chunk
        for chunk in chunks
        if not re.search(r"references|bibliography|acknowledg", str(chunk.heading_path), re.I)
    ] or chunks
    # Unstructured Markdown still gets coverage from beginning through end.
    spread = [
        scientific[round(index * (len(scientific) - 1) / max(1, limit - 1))]
        for index in range(limit)
    ]
    if len(representatives) > limit - 1:
        representatives = [
            representatives[round(index * (len(representatives) - 1) / max(1, limit - 2))]
            for index in range(limit - 1)
        ]
    return list({chunk.id: chunk for chunk in [chunks[0], *representatives, *spread]}.values())[
        :limit
    ]


def summary_context(
    database: Database, scope: RetrievalScope, chunks: list[DocumentChunk], settings: Settings
) -> tuple[list[RetrievalHit], dict | None, dict]:
    if not chunks or any(
        (chunk.document_id, chunk.chunk_set_id, chunk.parse_run_id)
        != (scope.document_id, scope.chunk_set_id, scope.parse_run_id)
        for chunk in chunks
    ):
        raise RagNotReady("Summary context does not match the current document")
    cached = None
    anchors: list[DocumentChunk] = []
    by_id = {chunk.id: chunk for chunk in chunks}
    try:
        summary = read_summary(database, scope.document_id, settings)
        if summary.document_id != scope.document_id or summary.chunk_set_id != scope.chunk_set_id:
            raise RagNotReady("Saved summary source changed")
        if not summary.unavailable_fields:
            candidate = summary.model_dump(include={*TEXT_FIELDS, "authors"})
            if (
                len(json.dumps(candidate, ensure_ascii=False).encode())
                <= settings.rag_context_bytes // 3
            ):
                cached = candidate
                for field in (*TEXT_FIELDS, "authors"):
                    source = next(
                        (source for source in summary.sources if source.field == field), None
                    )
                    if source is not None:
                        if source.chunk_id not in by_id:
                            raise RagNotReady("Saved summary source changed")
                        anchors.append(by_id[source.chunk_id])
    except (SummaryNotReady, SummaryError):
        pass  # Never run/retry the summary-generation workflow inside chat.
    samples = section_samples(chunks)
    selected = list({chunk.id: chunk for chunk in [*anchors, *samples]}.values())[:20]
    return (
        [RetrievalHit(chunk=chunk) for chunk in selected],
        cached,
        {
            "context_strategy": "saved_summary" if cached else "section_samples",
            "summary_reused": cached is not None,
            "total_document_chunks": len(chunks),
        },
    )
