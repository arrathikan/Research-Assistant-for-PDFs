"""Public citation resolution is deterministic and never invokes a provider."""

from unittest.mock import MagicMock, patch

import pytest
from backend.gateway.documents import get_database
from backend.gateway.main import app
from backend.services.rag_service.citations import InvalidCitation, StaleCitation, make_citation
from backend.shared.database import StorageUnavailable
from backend.shared.storage import DocumentNotFound
from backend.tests.test_citations import DOCUMENT_ID, QUOTE, anchored_chunks, selection
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "failure,status",
    [
        (None, 200),
        (InvalidCitation(), 422),
        (StaleCitation(), 409),
        (DocumentNotFound(), 404),
        (StorageUnavailable("safe failure"), 503),
    ],
)
def test_resolution_endpoint(failure, status):
    app.dependency_overrides[get_database] = lambda: MagicMock()
    try:
        with (
            patch(
                "backend.gateway.citations.resolve_citation",
                return_value=make_citation(anchored_chunks()[0], 1, QUOTE),
                side_effect=failure,
            ),
            patch("backend.services.rag_service.chain.OpenRouterClient") as model,
        ):
            with TestClient(app) as client:
                response = client.post(
                    f"/api/v1/documents/{DOCUMENT_ID}/citations/resolve",
                    json=selection().model_dump(),
                )
            assert response.status_code == status
            model.assert_not_called()
            if status == 200:
                assert response.json()["bounding_boxes"][0]["renderable"]
    finally:
        app.dependency_overrides.clear()
