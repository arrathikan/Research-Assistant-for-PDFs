"""CLI and read-only extraction endpoint contracts with mocked boundaries."""

from unittest.mock import MagicMock, patch

import pytest
from backend.gateway.documents import get_database
from backend.gateway.main import app
from backend.services.document_processor.extraction import ParsingNotReady
from backend.services.document_processor.main import main
from backend.services.document_processor.parsed_models import ParsedDocument, ParsedPage
from backend.shared.config import Settings
from backend.shared.storage import DocumentNotFound
from fastapi.testclient import TestClient

DOCUMENT_ID = "507f1f77bcf86cd799439011"


def result():
    return ParsedDocument(
        document_id=DOCUMENT_ID,
        pages=[ParsedPage(document_id=DOCUMENT_ID, page_number=1, markdown="# Paper")],
    )


def test_cli_missing_key_never_connects_to_database():
    with (
        patch(
            "backend.services.document_processor.main.get_settings",
            return_value=Settings(_env_file=None, llama_cloud_api_key=""),
        ),
        patch("backend.services.document_processor.main.connect_database") as connect,
    ):
        assert main([DOCUMENT_ID]) == 1
        connect.assert_not_called()


def test_cli_runs_one_document():
    with (
        patch(
            "backend.services.document_processor.main.get_settings",
            return_value=Settings(_env_file=None, llama_cloud_api_key="test"),
        ),
        patch("backend.services.document_processor.main.connect_database") as connect,
        patch("backend.services.document_processor.main.parse_pdf", return_value=result()) as parse,
    ):
        assert main([DOCUMENT_ID]) == 0
        assert parse.call_args.args[1] == DOCUMENT_ID
        connect.return_value.__exit__.assert_called_once()


def test_cli_validates_identifier_before_opening_database():
    with patch("backend.services.document_processor.main.connect_database") as connect:
        with pytest.raises(SystemExit) as error:
            main(["invalid-id"])
        assert error.value.code == 2
        connect.assert_not_called()


@pytest.mark.parametrize(
    "failure,code", [(None, 200), (ParsingNotReady(), 409), (DocumentNotFound(), 404)]
)
def test_parsed_endpoint(failure, code):
    app.dependency_overrides[get_database] = lambda: MagicMock()
    try:
        with patch(
            "backend.gateway.documents.read_parsed_document",
            return_value=result(),
            side_effect=failure,
        ):
            with TestClient(app) as client:
                response = client.get(f"/api/v1/documents/{DOCUMENT_ID}/parsed")
                assert response.status_code == code
                if code == 200:
                    assert response.json()["pages"][0]["markdown"] == "# Paper"
    finally:
        app.dependency_overrides.clear()
