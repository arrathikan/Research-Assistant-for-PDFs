"""Voyage request contracts with real SDK result objects and mocked network."""

from unittest.mock import patch

import pytest
from backend.shared.config import Settings
from backend.shared.embedding_models import EmbeddingError, EmbeddingInputError, validate_vectors
from backend.shared.voyage import document_batches, embed_documents, embed_query, embedding_profile
from pydantic import ValidationError
from voyageai.error import AuthenticationError, RateLimitError
from voyageai.object.embeddings import EmbeddingsObject

SETTINGS = Settings(_env_file=None, voyage_api_key="test-only-key")


def response(count, dimensions=1024):
    result = EmbeddingsObject()
    result.embeddings = [[0.1] * dimensions for _ in range(count)]
    return result


def test_document_batches_and_request_parameters():
    settings = Settings(_env_file=None, voyage_api_key="test", voyage_batch_size=2)
    with patch("backend.shared.voyage.voyageai.Client") as constructor:
        constructor.return_value.embed.side_effect = [response(2), response(1)]
        vectors = embed_documents(["First", "Second", "Third"], settings)
    assert len(vectors) == 3
    constructor.assert_called_once_with(api_key="test", max_retries=0, timeout=30)
    assert [call.args[0] for call in constructor.return_value.embed.call_args_list] == [
        ["First", "Second"],
        ["Third"],
    ]
    assert constructor.return_value.embed.call_args.kwargs == {
        "model": "voyage-3",
        "input_type": "document",
        "truncation": False,
        "output_dtype": "float",
        "output_dimension": None,
    }


def test_query_uses_query_input_type_and_same_dimensions():
    with patch("backend.shared.voyage.voyageai.Client") as constructor:
        constructor.return_value.embed.return_value = response(1)
        assert len(embed_query("What is the method?", SETTINGS)) == 1024
        assert constructor.return_value.embed.call_args.kwargs["input_type"] == "query"


def test_voyage4_explicit_dimensions_are_supported():
    settings = Settings(
        _env_file=None, voyage_api_key="test", voyage_model="voyage-4", voyage_dimensions=512
    )
    with patch("backend.shared.voyage.voyageai.Client") as constructor:
        constructor.return_value.embed.return_value = response(1, 512)
        assert len(embed_query("Question", settings)) == 512
        assert constructor.return_value.embed.call_args.kwargs["output_dimension"] == 512


def test_empty_document_list_needs_no_key_or_call():
    with patch("backend.shared.voyage.voyageai.Client") as client:
        assert embed_documents([], Settings(_env_file=None, voyage_api_key="")) == []
        client.assert_not_called()


def test_invalid_inputs_are_checked_before_any_paid_request():
    settings = Settings(_env_file=None, voyage_max_input_bytes=4, voyage_max_batch_bytes=8)
    with patch("backend.shared.voyage.voyageai.Client") as client:
        for texts in [["ok", ""], ["ok", "too long"], ["   "]]:
            with pytest.raises(EmbeddingInputError):
                embed_documents(texts, settings)
        client.assert_not_called()
    assert list(document_batches(["aaaa", "bbbb", "cc"], settings)) == [["aaaa", "bbbb"], ["cc"]]


def test_missing_key_fails_without_calling_provider():
    with patch("backend.shared.voyage.voyageai.Client") as client:
        with pytest.raises(EmbeddingError, match="not configured"):
            embed_query("Question", Settings(_env_file=None, voyage_api_key=""))
        client.assert_not_called()


def test_rate_limit_retries_are_bounded_and_back_off():
    with (
        patch("backend.shared.voyage.voyageai.Client") as constructor,
        patch("backend.shared.voyage.time.sleep") as sleep,
    ):
        constructor.return_value.embed.side_effect = [
            RateLimitError("private"),
            RateLimitError("private"),
            response(1),
        ]
        assert len(embed_query("Question", SETTINGS)) == 1024
        assert constructor.return_value.embed.call_count == 3
        assert [call.args[0] for call in sleep.call_args_list] == [1, 2]


def test_retry_exhaustion_and_auth_failure_are_safe():
    with (
        patch("backend.shared.voyage.voyageai.Client") as constructor,
        patch("backend.shared.voyage.time.sleep"),
    ):
        constructor.return_value.embed.side_effect = RateLimitError("secret")
        with pytest.raises(
            EmbeddingError, match="^Voyage embedding request failed after bounded retries$"
        ):
            embed_query("Question", SETTINGS)
        assert constructor.return_value.embed.call_count == 3
        constructor.return_value.embed.side_effect = AuthenticationError("secret-key")
        constructor.return_value.embed.reset_mock()
        with pytest.raises(EmbeddingError, match="^Voyage embedding request failed$"):
            embed_query("Question", SETTINGS)
        assert constructor.return_value.embed.call_count == 1


@pytest.mark.parametrize(
    "raw,count,dimensions",
    [
        ([], 1, 2),
        ([[1]], 1, 2),
        ([[0, 0]], 1, 2),
        ([[float("nan"), 1]], 1, 2),
        ([[True, 1]], 1, 2),
        ([["bad", 1]], 1, 2),
    ],
)
def test_invalid_vectors_are_rejected(raw, count, dimensions):
    with pytest.raises(EmbeddingError):
        validate_vectors(raw, count, dimensions)


def test_profile_is_stable_and_dimension_model_settings_are_validated():
    assert embedding_profile(SETTINGS).id == embedding_profile(SETTINGS).id
    with pytest.raises(ValidationError):
        Settings(_env_file=None, voyage_model="voyage-3", voyage_dimensions=512)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, voyage_max_input_bytes=100, voyage_max_batch_bytes=50)


def test_embedding_dimension_is_loaded_from_environment(monkeypatch):
    monkeypatch.setenv("VOYAGE_DIMENSIONS", "1024")
    assert Settings(_env_file=None).voyage_dimensions == 1024
