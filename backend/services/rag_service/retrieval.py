"""Atlas dense/keyword retrieval, source isolation and Python reciprocal rank fusion."""

from hashlib import sha256

from backend.services.document_processor.chunk_models import DocumentChunk
from backend.services.document_processor.chunk_storage import ChunkingNotReady, read_document_chunks
from backend.services.document_processor.embedding_storage import (
    EmbeddingNotReady,
    read_embedding_summary,
)
from backend.services.rag_service.indexes import check_indexes
from backend.services.rag_service.models import (
    RagNotReady,
    RagUnavailable,
    RetrievalHit,
    RetrievalScope,
)
from backend.shared.config import Settings
from backend.shared.embedding_models import EmbeddingError, EmbeddingInputError
from backend.shared.voyage import embed_query
from langchain_core.runnables import RunnableLambda, RunnableParallel
from pymongo.database import Database
from pymongo.errors import PyMongoError


def current_scope(
    database: Database, document_id: str, settings: Settings
) -> tuple[RetrievalScope, list[DocumentChunk]]:
    try:
        summary = read_embedding_summary(database, document_id, settings)
    except EmbeddingNotReady:
        raise RagNotReady(
            "Complete embeddings for the current chunks and model before chatting"
        ) from None
    try:
        chunks = read_document_chunks(database, summary.document_id)
    except ChunkingNotReady:
        raise RagNotReady("Current chunks changed during retrieval") from None
    return RetrievalScope(
        document_id=summary.document_id,
        chunk_set_id=summary.chunk_set_id,
        parse_run_id=chunks[0].parse_run_id,
        embedding_profile_id=summary.embedding_profile_id,
    ), chunks


def rrf(
    dense: list[DocumentChunk], keyword: list[DocumentChunk], limit: int, constant: int = 60
) -> list[RetrievalHit]:
    if limit < 1 or constant < 1:
        raise ValueError("RRF limit and constant must be positive")
    scores: dict[str, float] = {}
    chunks: dict[str, DocumentChunk] = {}
    for results in [dense, keyword]:
        seen = set()
        for rank, chunk in enumerate(results, 1):
            if chunk.id in seen:
                continue
            seen.add(chunk.id)
            if chunk.id in chunks and chunks[chunk.id] != chunk:
                raise RagUnavailable("Retrieval returned inconsistent chunk identities")
            chunks[chunk.id] = chunk
            scores[chunk.id] = scores.get(chunk.id, 0) + 1 / (constant + rank)
    ordered = sorted(
        scores,
        key=lambda identifier: (-scores[identifier], chunks[identifier].chunk_index, identifier),
    )
    return [
        RetrievalHit(chunk=chunks[identifier], rrf_score=scores[identifier])
        for identifier in ordered[:limit]
    ]


def _results(
    database: Database, pipeline: list[dict], scope: RetrievalScope, chunks: list[DocumentChunk]
) -> list[DocumentChunk]:
    by_id = {chunk.id: chunk for chunk in chunks}
    result = []
    try:
        for record in database.chunk_embeddings.aggregate(pipeline):
            chunk = by_id.get(record.get("chunk_id"))
            if (
                chunk is None
                or any(record.get(key) != value for key, value in scope.filters().items())
                or record.get("content_sha256") != sha256(chunk.content.encode()).hexdigest()
            ):
                raise RagUnavailable(
                    "Search results did not match the selected document generation"
                )
            result.append(chunk)
    except PyMongoError:
        raise RagUnavailable(
            "Atlas retrieval unavailable; check search indexes and deployment support"
        ) from None
    return result


def _candidates(
    database: Database, document_id: str, question: str, settings: Settings
) -> tuple[RetrievalScope, list[DocumentChunk], list[DocumentChunk]]:
    scope, chunks = current_scope(database, document_id, settings)
    check_indexes(database, settings)  # Check readiness before a paid query embedding.
    try:
        vector = embed_query(question, settings)
    except (EmbeddingError, EmbeddingInputError):
        raise RagUnavailable("Voyage query embedding unavailable") from None
    fields = {"chunk_id": 1, "content_sha256": 1, **{key: 1 for key in scope.filters()}}
    dense = [
        {
            "$vectorSearch": {
                "index": settings.vector_search_index_name,
                "path": "embedding",
                "queryVector": vector,
                "numCandidates": max(settings.vector_num_candidates, 20 * settings.rag_candidate_k),
                "limit": settings.rag_candidate_k,
                "filter": scope.filters(),
            }
        },
        {"$match": scope.filters()},
        {"$project": fields},
    ]
    keyword = [
        {
            "$search": {
                "index": settings.keyword_search_index_name,
                "compound": {
                    "must": [{"text": {"query": question, "path": "chunk.content"}}],
                    "filter": [
                        {"equals": {"path": key, "value": value}}
                        for key, value in scope.filters().items()
                    ],
                },
            }
        },
        {"$match": scope.filters()},
        {"$limit": settings.rag_candidate_k},
        {"$project": fields},
    ]
    parallel = RunnableParallel(
        dense=RunnableLambda(lambda _: _results(database, dense, scope, chunks)),
        keyword=RunnableLambda(lambda _: _results(database, keyword, scope, chunks)),
    ).invoke(None)
    after, _ = current_scope(database, document_id, settings)
    if after != scope:
        raise RagNotReady("Document generation changed during retrieval")
    return scope, parallel["dense"], parallel["keyword"]


def _select(hits: list[RetrievalHit], limit: int, diversify: bool) -> list[RetrievalHit]:
    if not 1 <= limit <= 20:
        raise ValueError("Context limit must be between 1 and 20")
    if not diversify:
        return hits[:limit]
    selected, remaining, sections = [], [], set()
    for hit in hits:
        key = tuple(sorted(hit.chunk.heading_path.items())) or (
            ("page", str(hit.chunk.page_number)),
        )
        if key in sections:
            remaining.append(hit)
        else:
            sections.add(key)
            selected.append(hit)
    return (selected + remaining)[:limit]


def retrieve(
    database: Database,
    document_id: str,
    question: str,
    settings: Settings,
    *,
    context_limit: int | None = None,
    diversify: bool = False,
) -> tuple[RetrievalScope, list[RetrievalHit]]:
    scope, dense, keyword = _candidates(database, document_id, question, settings)
    ranked = rrf(dense, keyword, settings.rag_candidate_k * 2, settings.rag_rrf_constant)
    return scope, _select(ranked, context_limit or settings.rag_context_k, diversify)


def retrieve_variants(
    database: Database,
    document_id: str,
    question: str,
    settings: Settings,
    *,
    context_limit: int | None = None,
    diversify: bool = False,
) -> tuple[RetrievalScope, dict[str, list[RetrievalHit]]]:
    """Share one query vector/source snapshot; semantic ignores keyword ranks."""
    scope, dense, keyword = _candidates(database, document_id, question, settings)
    semantic = [
        RetrievalHit(chunk=chunk) for chunk in {chunk.id: chunk for chunk in dense}.values()
    ]
    hybrid = rrf(dense, keyword, settings.rag_candidate_k * 2, settings.rag_rrf_constant)
    limit = context_limit or settings.rag_context_k
    return scope, {
        "hybrid": _select(hybrid, limit, diversify),
        "semantic": _select(semantic, limit, diversify),
    }
