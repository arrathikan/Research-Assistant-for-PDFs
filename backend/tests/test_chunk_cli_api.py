"""Chunk command and published-chunk HTTP contracts with mocked boundaries."""

from unittest.mock import MagicMock, patch

import pytest
from backend.gateway.documents import get_database
from backend.gateway.main import app
from backend.services.document_processor.chunk_cli import main
from backend.services.document_processor.chunk_storage import ChunkingNotReady
from backend.services.document_processor.chunking import chunk_document
from backend.services.document_processor.parsed_models import ParsedDocument, ParsedPage
from backend.shared.config import Settings
from backend.shared.storage import DocumentNotFound
from fastapi.testclient import TestClient

ID = "507f1f77bcf86cd799439011"


def chunks():
    return chunk_document(
        ParsedDocument(
            document_id=ID,
            pages=[ParsedPage(document_id=ID, page_number=1, markdown="## Method\n\nEvidence")],
        ),
        "parse-a",
    )


def test_chunk_cli_needs_no_provider_key_and_accepts_overrides():
    with (
        patch(
            "backend.services.document_processor.chunk_cli.get_settings",
            return_value=Settings(_env_file=None, llama_cloud_api_key="", voyage_api_key=""),
        ),
        patch("backend.services.document_processor.chunk_cli.connect_database") as connect,
        patch(
            "backend.services.document_processor.chunk_cli.chunk_stored_document",
            return_value=chunks(),
        ) as chunk,
    ):
        assert main([ID, "--chunk-size", "80", "--chunk-overlap", "10"]) == 0
        assert chunk.call_args.args[2].chunk_size == 80
        assert chunk.call_args.args[2].chunk_overlap == 10
        connect.return_value.__exit__.assert_called_once()


def test_invalid_cli_configuration_does_not_connect():
    with patch("backend.services.document_processor.chunk_cli.connect_database") as connect:
        assert main([ID, "--chunk-size", "10", "--chunk-overlap", "10"]) == 1
        connect.assert_not_called()


def test_invalid_cli_identifier_is_rejected():
    with pytest.raises(SystemExit) as error:
        main(["invalid"])
    assert error.value.code == 2


@pytest.mark.parametrize(
    "failure,code", [(None, 200), (ChunkingNotReady(), 409), (DocumentNotFound(), 404)]
)
def test_chunk_endpoint(failure, code):
    app.dependency_overrides[get_database] = lambda: MagicMock()
    try:
        with patch(
            "backend.gateway.documents.read_document_chunks",
            return_value=chunks(),
            side_effect=failure,
        ):
            with TestClient(app) as client:
                response = client.get(f"/api/v1/documents/{ID}/chunks")
        assert response.status_code == code
        if code == 200:
            assert response.json()[0]["id"] == chunks()[0].id
            assert "_id" not in response.json()[0]
            assert response.json()[0]["page_spans"][0]["page_number"] == 1
    finally:
        app.dependency_overrides.clear()
