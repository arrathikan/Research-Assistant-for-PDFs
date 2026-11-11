"""Public chat response excludes private retrieval/evaluation fields."""

from unittest.mock import MagicMock, patch

import pytest
from backend.gateway.documents import get_database
from backend.gateway.main import app
from backend.services.rag_service.models import RagConflict, RagNotReady, RagUnavailable
from backend.shared.storage import DocumentNotFound
from backend.tests.test_rag_chain import DOCUMENT_ID, run
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "failure,status",
    [
        (None, 200),
        (DocumentNotFound(), 404),
        (RagNotReady(), 409),
        (RagConflict(), 409),
        (RagUnavailable("private detail"), 503),
    ],
)
def test_chat_response_and_errors(failure, status):
    output = run()
    app.dependency_overrides[get_database] = lambda: MagicMock()
    try:
        with patch(
            "backend.gateway.chat.chat_with_trace", return_value=output, side_effect=failure
        ):
            with TestClient(app) as client:
                response = client.post(
                    f"/api/v1/documents/{DOCUMENT_ID}/chat", json={"message": "Question"}
                )
        assert response.status_code == status
        assert "private detail" not in response.text
        assert "retrieved_contexts" not in response.text
        if status == 200:
            assert response.json()["citations"][0]["document_id"] == DOCUMENT_ID
    finally:
        app.dependency_overrides.clear()


def test_empty_question_is_rejected_before_pipeline():
    app.dependency_overrides[get_database] = lambda: MagicMock()
    try:
        with patch("backend.gateway.chat.chat_with_trace") as chat:
            with TestClient(app) as client:
                assert (
                    client.post(
                        f"/api/v1/documents/{DOCUMENT_ID}/chat", json={"message": "  "}
                    ).status_code
                    == 422
                )
            chat.assert_not_called()
    finally:
        app.dependency_overrides.clear()
