"""Opt-in provider/Atlas checks. Synthetic input only; never run in ordinary CI."""

import os
import time
from uuid import uuid4

import pytest
from backend.services.document_processor.chunk_storage import chunk_stored_document
from backend.services.document_processor.embedding_storage import embed_stored_document
from backend.services.rag_service.chain import answer_with_trace
from backend.services.rag_service.indexes import check_indexes
from backend.services.rag_service.models import (
    ChatRequest,
    RagUnavailable,
    RetrievalHit,
    RetrievalScope,
)
from backend.services.rag_service.service import chat_with_trace
from backend.shared.config import get_settings
from backend.shared.database import connect_database, ensure_indexes
from backend.shared.voyage import embedding_profile
from backend.tests.summary_fixtures import summary_chunks
from backend.tests.test_chunking_integration import seed_parse

pytestmark = pytest.mark.live_rag


def test_live_openrouter_grounded_answer():
    if os.environ.get("RESEARCHAI_RUN_ANSWER_LIVE") != "1":
        pytest.skip("Set RESEARCHAI_RUN_ANSWER_LIVE=1 for a paid answer check")
    settings = get_settings()
    if not settings.openrouter_api_key.strip() or settings.openrouter_api_key.startswith("your_"):
        pytest.skip("OpenRouter key is not configured")
    chunks = summary_chunks()
    scope = RetrievalScope(
        document_id=chunks[0].document_id,
        chunk_set_id=chunks[0].chunk_set_id,
        parse_run_id=chunks[0].parse_run_id,
        embedding_profile_id=embedding_profile(settings).id,
    )
    result = answer_with_trace(
        "What is the synthetic counter result?",
        scope,
        [RetrievalHit(chunk=chunk) for chunk in chunks],
        settings,
        uuid4().hex,
        uuid4().hex,
    )
    assert not result.response.is_out_of_scope
    assert "42" in result.response.answer
    assert result.response.citations


def test_live_atlas_hybrid_chat_document_isolation():
    if os.environ.get("RESEARCHAI_RUN_RAG_LIVE") != "1":
        pytest.skip("Set RESEARCHAI_RUN_RAG_LIVE=1 for paid Atlas/Voyage/OpenRouter integration")
    uri = os.environ.get("RESEARCHAI_TEST_ATLAS_URI")
    if not uri:
        pytest.skip("Set RESEARCHAI_TEST_ATLAS_URI; never use a production database name")
    settings = get_settings().model_copy(
        update={"mongodb_uri": uri, "mongodb_db_name": "researchai_test_" + uuid4().hex}
    )
    with connect_database(settings) as db:
        try:
            ensure_indexes(db)
            first, second = seed_parse(db), seed_parse(db)
            for identifier in [first, second]:
                chunk_stored_document(db, identifier, settings)
                embed_stored_document(db, identifier, settings)
            check_indexes(db, settings, create=True)
            deadline = time.monotonic() + 180
            while True:
                try:
                    check_indexes(db, settings)
                    break
                except RagUnavailable:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(2)
            output = chat_with_trace(
                db,
                first,
                ChatRequest(message="What score is shown for model A in the results table?"),
                settings,
            )
            assert output.response.citations and "42" in output.response.answer
            assert all(citation.document_id == first for citation in output.response.citations)
            assert db.chat_turns.count_documents({"document_id": second}) == 0
        finally:
            db.client.drop_database(db.name)
