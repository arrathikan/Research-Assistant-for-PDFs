"""Atlas query/filter contracts, index safety and actual RRF calculations."""

from hashlib import sha256
from unittest.mock import MagicMock, patch

import pytest
from backend.services.rag_service.indexes import check_indexes, definitions
from backend.services.rag_service.models import RagNotReady, RagUnavailable, RetrievalScope
from backend.services.rag_service.retrieval import retrieve, retrieve_variants, rrf
from backend.shared.config import Settings
from backend.tests.summary_fixtures import DOCUMENT_ID, summary_chunks

SETTINGS = Settings(_env_file=None)
CHUNKS = summary_chunks()
SCOPE = RetrievalScope(
    document_id=DOCUMENT_ID,
    chunk_set_id=CHUNKS[0].chunk_set_id,
    parse_run_id=CHUNKS[0].parse_run_id,
    embedding_profile_id="a" * 64,
)


def record():
    return {
        **SCOPE.filters(),
        "chunk_id": CHUNKS[0].id,
        "content_sha256": sha256(CHUNKS[0].content.encode()).hexdigest(),
    }


def test_indexes_include_vector_dimensions_and_explicit_bm25_filters():
    vector, keyword = definitions(SETTINGS)
    assert vector["definition"]["fields"][0]["numDimensions"] == 1024
    assert {field["path"] for field in vector["definition"]["fields"][1:]} == set(SCOPE.filters())
    assert keyword["definition"]["mappings"]["fields"]["chunk"]["fields"]["content"][
        "similarity"
    ] == {"type": "bm25"}


@pytest.mark.parametrize("state", ["missing", "building", "incompatible"])
def test_unready_indexes_fail_without_overwriting_them(state):
    db = MagicMock()
    definition = definitions(SETTINGS)[0]["definition"]
    if state == "missing":
        db.chunk_embeddings.list_search_indexes.return_value = []
    else:
        db.chunk_embeddings.list_search_indexes.return_value = [
            {
                "queryable": state != "building",
                "latestDefinition": {} if state == "incompatible" else definition,
            }
        ]
    with pytest.raises(RagUnavailable):
        check_indexes(db, SETTINGS)
    db.chunk_embeddings.create_search_index.assert_not_called()


def test_explicit_creation_does_not_recreate_existing_indexes():
    db = MagicMock()
    db.chunk_embeddings.list_search_indexes.side_effect = [
        [{"queryable": True, "latestDefinition": definitions(SETTINGS)[0]["definition"]}],
        [],
    ]
    check_indexes(db, SETTINGS, create=True)
    db.chunk_embeddings.create_search_index.assert_called_once()


def test_rrf_uses_ranks_and_deduplicates_each_branch():
    a, b = CHUNKS[0], summary_chunks(text="# Alternate\n\nOther synthetic evidence.")[0]
    result = rrf([a, a, b], [b, a], 2)
    assert len(result) == 2
    assert result[0].chunk == a
    assert result[0].rrf_score == pytest.approx(1 / 61 + 1 / 62)
    assert result[1].rrf_score == pytest.approx(1 / 63 + 1 / 61)
    assert rrf([], [], 5) == []


def test_dense_and_keyword_queries_pre_filter_the_same_generation():
    db = MagicMock()
    db.chunk_embeddings.aggregate.return_value = [record()]
    with (
        patch("backend.services.rag_service.retrieval.current_scope", return_value=(SCOPE, CHUNKS)),
        patch("backend.services.rag_service.retrieval.check_indexes"),
        patch("backend.services.rag_service.retrieval.embed_query", return_value=[0.1] * 1024),
    ):
        scope, hits = retrieve(db, DOCUMENT_ID, "synthetic method", SETTINGS)
    assert scope == SCOPE and hits[0].chunk == CHUNKS[0]
    pipelines = [call.args[0] for call in db.chunk_embeddings.aggregate.call_args_list]
    dense = next(p for p in pipelines if "$vectorSearch" in p[0])
    keyword = next(p for p in pipelines if "$search" in p[0])
    assert dense[0]["$vectorSearch"]["filter"] == SCOPE.filters()
    assert dense[0]["$vectorSearch"]["numCandidates"] >= 20 * SETTINGS.rag_candidate_k
    assert keyword[0]["$search"]["compound"]["filter"] == [
        {"equals": {"path": k, "value": v}} for k, v in SCOPE.filters().items()
    ]
    assert dense[1] == keyword[1] == {"$match": SCOPE.filters()}


@pytest.mark.parametrize(
    "mutation", ["other_document", "wrong_set", "wrong_profile", "bad_hash", "unknown_chunk"]
)
def test_cross_document_or_corrupt_search_hits_are_rejected(mutation):
    db = MagicMock()
    bad = record()
    if mutation == "other_document":
        bad["document_id"] = "507f1f77bcf86cd799439012"
    if mutation == "wrong_set":
        bad["chunk_set_id"] = "b" * 64
    if mutation == "wrong_profile":
        bad["embedding_profile_id"] = "b" * 64
    if mutation == "bad_hash":
        bad["content_sha256"] = "b" * 64
    if mutation == "unknown_chunk":
        bad["chunk_id"] = "b" * 64
    db.chunk_embeddings.aggregate.return_value = [bad]
    with (
        patch("backend.services.rag_service.retrieval.current_scope", return_value=(SCOPE, CHUNKS)),
        patch("backend.services.rag_service.retrieval.check_indexes"),
        patch("backend.services.rag_service.retrieval.embed_query", return_value=[0.1] * 1024),
    ):
        with pytest.raises(RagUnavailable):
            retrieve(db, DOCUMENT_ID, "question", SETTINGS)


def test_index_failure_prevents_paid_embedding():
    with (
        patch("backend.services.rag_service.retrieval.current_scope", return_value=(SCOPE, CHUNKS)),
        patch("backend.services.rag_service.retrieval.check_indexes", side_effect=RagUnavailable()),
        patch("backend.services.rag_service.retrieval.embed_query") as embed,
    ):
        with pytest.raises(RagUnavailable):
            retrieve(MagicMock(), DOCUMENT_ID, "question", SETTINGS)
        embed.assert_not_called()


def test_generation_change_during_search_rejects_stale_results():
    db = MagicMock()
    db.chunk_embeddings.aggregate.return_value = []
    after = SCOPE.model_copy(update={"chunk_set_id": "b" * 64})
    with (
        patch(
            "backend.services.rag_service.retrieval.current_scope",
            side_effect=[(SCOPE, CHUNKS), (after, CHUNKS)],
        ),
        patch("backend.services.rag_service.retrieval.check_indexes"),
        patch("backend.services.rag_service.retrieval.embed_query", return_value=[0.1] * 1024),
    ):
        with pytest.raises(RagNotReady):
            retrieve(db, DOCUMENT_ID, "question", SETTINGS)


def test_paired_strategies_share_one_query_vector_and_keep_semantic_vector_order():
    db = MagicMock()
    db.chunk_embeddings.aggregate.return_value = [record()]
    with (
        patch("backend.services.rag_service.retrieval.current_scope", return_value=(SCOPE, CHUNKS)),
        patch("backend.services.rag_service.retrieval.check_indexes"),
        patch(
            "backend.services.rag_service.retrieval.embed_query", return_value=[0.1] * 1024
        ) as embed,
    ):
        scope, variants = retrieve_variants(db, DOCUMENT_ID, "synthetic question", SETTINGS)
    embed.assert_called_once()
    assert scope == SCOPE
    assert variants["semantic"][0].chunk == variants["hybrid"][0].chunk == CHUNKS[0]
    assert variants["semantic"][0].rrf_score == 0


def test_broad_context_selection_covers_sections_before_repeating_one_section():
    from backend.services.rag_service.models import RetrievalHit
    from backend.services.rag_service.retrieval import _select

    a = CHUNKS[0].model_copy(update={"heading_path": {"h2": "Methods"}})
    b = summary_chunks(text="# Methods\n\nSecond evidence passage.")[0].model_copy(
        update={"heading_path": {"h2": "Methods"}}
    )
    c = summary_chunks(text="# Results\n\nA different section.")[0].model_copy(
        update={"heading_path": {"h2": "Results"}}
    )
    hits = [RetrievalHit(chunk=chunk) for chunk in [a, b, c]]
    assert [hit.chunk.id for hit in _select(hits, 2, True)] == [a.id, c.id]
    assert [hit.chunk.id for hit in _select(hits, 2, False)] == [a.id, b.id]
