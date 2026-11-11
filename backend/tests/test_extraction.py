"""Extraction orchestration and publication tests use mocked storage/provider boundaries."""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from backend.services.document_processor.extraction import (
    ParsingConflict,
    ParsingNotReady,
    parse_pdf,
    read_parsed_document,
    save_parsed_document,
)
from backend.services.document_processor.parsed_models import (
    ParsedDocument,
    ParsedPage,
    ParsingError,
    SourceElement,
)
from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable
from backend.shared.models import ParsingStatus
from backend.shared.storage import DocumentNotFound, StoredDocument
from bson import ObjectId
from pymongo.errors import OperationFailure
from pypdf import PdfWriter

DOCUMENT_ID = "507f1f77bcf86cd799439011"
SETTINGS = Settings(_env_file=None, llama_cloud_api_key="test-only-key")


@pytest.fixture
def pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=300)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def document(pdf, **values):
    return StoredDocument(
        id=DOCUMENT_ID,
        gridfs_file_id=str(ObjectId()),
        sha256="a" * 64,
        filename="paper.pdf",
        file_size_bytes=len(pdf),
        page_count=1,
        **values,
    )


def parsed():
    return ParsedDocument(
        document_id=DOCUMENT_ID,
        provider_job_id="synthetic-job",
        pages=[
            ParsedPage(
                document_id=DOCUMENT_ID,
                page_number=1,
                markdown="# Paper",
                elements=[
                    SourceElement(
                        element_id=DOCUMENT_ID + ":p1:e0",
                        document_id=DOCUMENT_ID,
                        page_number=1,
                        element_index=0,
                        kind="heading",
                        source="items",
                        markdown="# Paper",
                    )
                ],
            )
        ],
    )


def test_parse_loads_original_and_publishes_complete_output(pdf):
    database = MagicMock()
    database.documents.find_one_and_update.return_value = {"_id": ObjectId(DOCUMENT_ID)}
    database.documents.update_one.return_value.matched_count = 1
    result = parsed()
    with (
        patch(
            "backend.services.document_processor.extraction.get_document",
            return_value=document(pdf),
        ),
        patch("backend.services.document_processor.extraction.read_pdf", return_value=pdf) as read,
        patch(
            "backend.services.document_processor.extraction.parse_with_llamaparse",
            return_value=result,
        ) as provider,
    ):
        assert parse_pdf(database, DOCUMENT_ID, SETTINGS) == result
    read.assert_called_once_with(database, DOCUMENT_ID)
    provider.assert_called_once_with(DOCUMENT_ID, pdf, 1, SETTINGS)
    database.parsed_pages.insert_many.assert_called_once()
    database.source_elements.insert_many.assert_called_once()
    committed = database.documents.update_one.call_args.args[1]["$set"]
    assert committed["parsing_status"] == "COMPLETED"
    assert committed["status"] == "PENDING"
    assert committed["active_parse_run_id"]
    assert database.documents.find_one_and_update.call_args.args[0]["parsing_status"] == {
        "$nin": [ParsingStatus.RUNNING, ParsingStatus.COMPLETED]
    }


def test_provider_failure_sets_safe_failed_status(pdf):
    database = MagicMock()
    with (
        patch(
            "backend.services.document_processor.extraction.get_document",
            return_value=document(pdf),
        ),
        patch("backend.services.document_processor.extraction.read_pdf", return_value=pdf),
        patch(
            "backend.services.document_processor.extraction.parse_with_llamaparse",
            side_effect=RuntimeError("secret-provider-detail"),
        ),
    ):
        with pytest.raises(ParsingError, match="^PDF parsing failed;"):
            parse_pdf(database, DOCUMENT_ID, SETTINGS)
    update = database.documents.update_one.call_args.args[1]["$set"]
    assert update["parsing_status"] == "FAILED"
    assert "secret" not in update["error_message"]
    database.parsed_pages.insert_many.assert_not_called()


def test_corrupt_original_is_rejected_without_provider_call(pdf):
    database = MagicMock()
    with (
        patch(
            "backend.services.document_processor.extraction.get_document",
            return_value=document(pdf),
        ),
        patch("backend.services.document_processor.extraction.read_pdf", return_value=b"corrupt"),
        patch("backend.services.document_processor.extraction.parse_with_llamaparse") as provider,
    ):
        with pytest.raises(ParsingError):
            parse_pdf(database, DOCUMENT_ID, SETTINGS)
        provider.assert_not_called()
    assert database.documents.update_one.call_args.args[1]["$set"]["status"] == "FAILED"


def test_active_claim_prevents_a_second_provider_call(pdf):
    database = MagicMock()
    database.documents.find_one_and_update.return_value = None
    with (
        patch(
            "backend.services.document_processor.extraction.get_document",
            return_value=document(pdf),
        ),
        patch("backend.services.document_processor.extraction.parse_with_llamaparse") as provider,
    ):
        with pytest.raises(ParsingConflict):
            parse_pdf(database, DOCUMENT_ID, SETTINGS)
        provider.assert_not_called()
    database.documents.update_one.assert_not_called()


def test_completed_parse_is_reused_without_key_or_provider_call(pdf):
    database = MagicMock()
    with (
        patch(
            "backend.services.document_processor.extraction.get_document",
            return_value=document(pdf, parsing_status=ParsingStatus.COMPLETED),
        ),
        patch(
            "backend.services.document_processor.extraction.read_parsed_document",
            return_value=parsed(),
        ) as read,
        patch("backend.services.document_processor.extraction.parse_with_llamaparse") as provider,
    ):
        assert (
            parse_pdf(database, DOCUMENT_ID, Settings(_env_file=None, llama_cloud_api_key=""))
            == parsed()
        )
        read.assert_called_once_with(database, DOCUMENT_ID)
        provider.assert_not_called()


def test_unconfigured_parser_leaves_document_unchanged(pdf):
    database = MagicMock()
    with patch(
        "backend.services.document_processor.extraction.get_document", return_value=document(pdf)
    ):
        with pytest.raises(ParsingError, match="not configured"):
            parse_pdf(database, DOCUMENT_ID, Settings(_env_file=None, llama_cloud_api_key=""))
    database.documents.find_one_and_update.assert_not_called()


def test_unknown_document_does_not_call_provider():
    with patch("backend.services.document_processor.extraction.get_document", return_value=None):
        with pytest.raises(DocumentNotFound):
            parse_pdf(MagicMock(), DOCUMENT_ID, SETTINGS)


def test_partial_storage_failure_never_publishes_pointer():
    database = MagicMock()
    database.source_elements.insert_many.side_effect = OperationFailure("private")
    with pytest.raises(StorageUnavailable):
        save_parsed_document(database, parsed(), "run-test", SETTINGS)
    database.documents.update_one.assert_not_called()


def test_lost_ownership_does_not_publish_success():
    database = MagicMock()
    database.documents.update_one.return_value.matched_count = 0
    with pytest.raises(ParsingConflict):
        save_parsed_document(database, parsed(), "run-test", SETTINGS)


def test_cross_document_sources_are_rejected_before_writing():
    database = MagicMock()
    data = parsed()
    data.pages[0].elements[0].document_id = str(ObjectId())
    with pytest.raises(ParsingError):
        save_parsed_document(database, data, "run-test", SETTINGS)
    database.parsed_pages.insert_many.assert_not_called()


def test_read_only_uses_committed_run_and_reconstructs_sources():
    database = MagicMock()
    database.documents.find_one.return_value = {
        "_id": ObjectId(DOCUMENT_ID),
        "active_parse_run_id": "committed",
        "page_count": 1,
    }
    data = parsed()
    database.parsed_pages.find.return_value.sort.return_value = [
        data.pages[0].model_dump(exclude={"elements"})
    ]
    database.source_elements.find.return_value.sort.return_value = [
        data.pages[0].elements[0].model_dump()
    ]
    result = read_parsed_document(database, DOCUMENT_ID)
    assert result.pages[0].elements[0].markdown == "# Paper"
    database.parsed_pages.find.assert_called_once_with(
        {"document_id": DOCUMENT_ID, "parse_run_id": "committed"}
    )


@pytest.mark.parametrize(
    "record,error", [(None, DocumentNotFound), ({"_id": ObjectId(DOCUMENT_ID)}, ParsingNotReady)]
)
def test_unpublished_content_is_not_returned(record, error):
    database = MagicMock()
    database.documents.find_one.return_value = record
    with pytest.raises(error):
        read_parsed_document(database, DOCUMENT_ID)
