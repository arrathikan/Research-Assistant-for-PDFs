"""Real isolated MongoDB persistence; the paid parser is explicitly mocked."""

import os
from io import BytesIO
from unittest.mock import patch
from uuid import uuid4

import pytest
from backend.gateway.documents import get_database
from backend.gateway.main import app
from backend.services.document_processor.extraction import (
    ParsingConflict,
    ParsingNotReady,
    parse_pdf,
    read_parsed_document,
)
from backend.services.document_processor.normalization import normalize_parsed_pages
from backend.services.document_processor.parsed_models import ParsingError
from backend.shared.config import Settings
from backend.shared.database import connect_database, ensure_indexes
from backend.shared.storage import get_document, store_pdf
from bson import ObjectId
from fastapi.testclient import TestClient
from pypdf import PdfWriter

pytestmark = pytest.mark.integration
SETTINGS = Settings(_env_file=None, llama_cloud_api_key="test-only-key")


@pytest.fixture
def database():
    uri = os.environ.get("RESEARCHAI_TEST_MONGODB_URI")
    if not uri:
        pytest.skip("Set RESEARCHAI_TEST_MONGODB_URI for real MongoDB tests")
    config = Settings(
        _env_file=None, mongodb_uri=uri, mongodb_db_name="researchai_test_" + uuid4().hex
    )
    with connect_database(config) as db:
        try:
            ensure_indexes(db)
            yield db
        finally:
            db.client.drop_database(db.name)


def upload(database):
    output = BytesIO()
    writer = PdfWriter()
    for _ in range(2):
        writer.add_blank_page(width=200, height=300)
    writer.write(output)
    return store_pdf(database, "synthetic.pdf", output.getvalue(), page_count=2).document.id


def output(identifier):
    return normalize_parsed_pages(
        identifier,
        [
            {
                "job_id": "mocked-provider-job",
                "pages": [
                    {
                        "page": 1,
                        "md": "# Synthetic Paper\n\nText",
                        "items": [
                            {
                                "type": "heading",
                                "text": "Synthetic Paper",
                                "md": "# Synthetic Paper",
                            }
                        ],
                    },
                    {"page": 2, "md": "## Results\n\n| A | B |\n| --- | --- |\n| 1 | 2 |"},
                ],
            }
        ],
        2,
    )


def test_real_parse_persistence_and_read_endpoint(database):
    identifier = upload(database)
    parsed = output(identifier)
    with patch(
        "backend.services.document_processor.extraction.parse_with_llamaparse", return_value=parsed
    ) as provider:
        assert parse_pdf(database, identifier, SETTINGS) == parsed
        assert parse_pdf(database, identifier, SETTINGS) == parsed
        provider.assert_called_once()
    metadata = get_document(database, identifier)
    assert metadata.parsing_status == "COMPLETED" and metadata.status == "PENDING"
    assert metadata.parsed_at is not None
    assert read_parsed_document(database, identifier) == parsed
    assert database.parsed_pages.count_documents({"document_id": identifier}) == 2
    assert database.source_elements.count_documents({"document_id": identifier}) == 1
    app.dependency_overrides[get_database] = lambda: database
    try:
        with TestClient(app) as client:
            response = client.get(f"/api/v1/documents/{identifier}/parsed")
            assert response.status_code == 200
            assert response.json()["pages"][1]["page_number"] == 2
    finally:
        app.dependency_overrides.clear()


def test_failure_is_safe_and_retry_publishes_new_complete_run(database):
    identifier = upload(database)
    with patch(
        "backend.services.document_processor.extraction.parse_with_llamaparse",
        side_effect=RuntimeError("provider-secret"),
    ):
        with pytest.raises(ParsingError):
            parse_pdf(database, identifier, SETTINGS)
    failed = get_document(database, identifier)
    assert failed.parsing_status == "FAILED" and failed.status == "FAILED"
    assert "secret" not in failed.error_message
    with pytest.raises(ParsingNotReady):
        read_parsed_document(database, identifier)
    with patch(
        "backend.services.document_processor.extraction.parse_with_llamaparse",
        return_value=output(identifier),
    ):
        parse_pdf(database, identifier, SETTINGS)
    assert get_document(database, identifier).parsing_status == "COMPLETED"


def test_unpublished_partial_run_is_invisible_and_running_claim_blocks_provider(database):
    identifier = upload(database)
    database.parsed_pages.insert_one(
        {
            "document_id": identifier,
            "parse_run_id": "unfinished",
            "page_number": 1,
            "markdown": "partial",
        }
    )
    with pytest.raises(ParsingNotReady):
        read_parsed_document(database, identifier)
    database.documents.update_one(
        {"_id": ObjectId(identifier)},
        {
            "$set": {
                "status": "PARSING",
                "parsing_status": "RUNNING",
                "parsing_run_id": "another-worker",
            }
        },
    )
    with patch("backend.services.document_processor.extraction.parse_with_llamaparse") as provider:
        with pytest.raises(ParsingConflict):
            parse_pdf(database, identifier, SETTINGS)
        provider.assert_not_called()


def test_parse_results_are_isolated_by_document_and_active_run(database):
    first, second = upload(database), None
    # Create a second, distinct PDF by adding metadata to the writer.
    output_bytes = BytesIO()
    writer = PdfWriter()
    for _ in range(2):
        writer.add_blank_page(width=200, height=300)
    writer.add_metadata({"/Title": "Second synthetic paper"})
    writer.write(output_bytes)
    second = store_pdf(database, "second.pdf", output_bytes.getvalue(), page_count=2).document.id
    for identifier in (first, second):
        with patch(
            "backend.services.document_processor.extraction.parse_with_llamaparse",
            return_value=output(identifier),
        ):
            parse_pdf(database, identifier, SETTINGS)
    result = read_parsed_document(database, first)
    assert all(page.document_id == first for page in result.pages)
    assert all(element.document_id == first for page in result.pages for element in page.elements)
