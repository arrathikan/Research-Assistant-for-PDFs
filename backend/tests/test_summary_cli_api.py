"""Read-only summary API and explicit generation command contracts."""

import json
from unittest.mock import MagicMock, patch

import pytest
from backend.gateway.documents import get_database
from backend.gateway.main import app
from backend.services.summary_service.main import main
from backend.services.summary_service.models import SummaryError, public_summary, validate_draft
from backend.services.summary_service.storage import SummaryNotReady
from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable
from backend.shared.storage import DocumentNotFound
from backend.tests.summary_fixtures import DOCUMENT_ID, summary_chunks, summary_draft
from fastapi.testclient import TestClient

SETTINGS = Settings(_env_file=None)


def test_generation_command_passes_id_and_closes_connection():
    with (
        patch("backend.services.summary_service.main.connect_database") as connect,
        patch("backend.services.summary_service.main.summarize_stored_document") as generate,
    ):
        assert main([DOCUMENT_ID]) == 0
        assert generate.call_args.args[1] == DOCUMENT_ID
        connect.return_value.__exit__.assert_called_once()


def test_generation_command_invalid_id_does_not_connect():
    with patch("backend.services.summary_service.main.connect_database") as connect:
        with pytest.raises(SystemExit) as error:
            main(["bad-id"])
        assert error.value.code == 2
        connect.assert_not_called()


def test_generation_command_reports_safe_failure():
    with (
        patch("backend.services.summary_service.main.connect_database"),
        patch(
            "backend.services.summary_service.main.summarize_stored_document",
            side_effect=SummaryError("safe failure"),
        ),
    ):
        assert main([DOCUMENT_ID]) == 1


@pytest.mark.parametrize(
    "failure,code",
    [
        (None, 200),
        (DocumentNotFound(), 404),
        (SummaryNotReady(), 409),
        (SummaryError("private"), 503),
        (StorageUnavailable("safe unavailable"), 503),
    ],
)
def test_read_endpoint_and_safe_errors_never_trigger_generation(failure, code):
    result = public_summary(
        validate_draft(json.dumps(summary_draft()), summary_chunks()), summary_chunks(), SETTINGS
    )
    app.dependency_overrides[get_database] = lambda: MagicMock()
    try:
        with (
            patch(
                "backend.gateway.documents.read_summary", return_value=result, side_effect=failure
            ),
            patch("backend.services.summary_service.storage.generate_summary") as generate,
        ):
            with TestClient(app) as client:
                response = client.get(f"/api/v1/documents/{DOCUMENT_ID}/summary")
            assert response.status_code == code
            assert "private" not in response.text
            generate.assert_not_called()
            if code == 200:
                assert response.json()["sources"][0]["chunk_id"] == summary_chunks()[0].id
                assert response.json()["document_id"] == DOCUMENT_ID
    finally:
        app.dependency_overrides.clear()
