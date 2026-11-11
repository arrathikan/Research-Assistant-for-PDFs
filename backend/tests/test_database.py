"""Database lifecycle/index contracts; these tests use mocked drivers."""

from unittest.mock import MagicMock, patch

import pytest
from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable, connect_database, ensure_indexes
from pydantic import ValidationError
from pymongo.errors import ConnectionFailure, OperationFailure


def test_connection_configuration_and_close():
    settings = Settings(_env_file=None, mongodb_timeout_ms=1234)
    with patch("backend.shared.database.MongoClient") as constructor:
        client = constructor.return_value
        with connect_database(settings) as database:
            assert database is client[settings.mongodb_db_name]
            client.admin.command.assert_called_once_with("ping")
        client.close.assert_called_once()
        assert constructor.call_args.kwargs == {
            "serverSelectionTimeoutMS": 1234,
            "connectTimeoutMS": 1234,
            "socketTimeoutMS": 1234,
            "tz_aware": True,
        }


def test_failed_ping_closes_client_and_hides_driver_message():
    with patch("backend.shared.database.MongoClient") as constructor:
        constructor.return_value.admin.command.side_effect = ConnectionFailure("secret-uri")
        with pytest.raises(StorageUnavailable, match="^MongoDB operation unavailable$"):
            with connect_database(Settings(_env_file=None)):
                pytest.fail("Failed ping must not yield a database")
        constructor.return_value.close.assert_called_once()


def test_operation_failure_closes_client():
    with patch("backend.shared.database.MongoClient") as constructor:
        with pytest.raises(StorageUnavailable):
            with connect_database(Settings(_env_file=None)):
                raise OperationFailure("private database detail")
        constructor.return_value.close.assert_called_once()


def test_indexes_cover_domain_collections_and_duplicate_safety():
    database = MagicMock()
    ensure_indexes(database)
    database.documents.create_index.assert_any_call("sha256", unique=True, name="unique_sha256")
    database.chunks.create_index.assert_called_once_with(
        [("document_id", 1), ("chunk_set_id", 1), ("chunk_index", 1)],
        unique=True,
        name="document_chunk_set_index",
    )
    for name in ("source_elements", "summaries", "chat_messages", "processing_jobs"):
        getattr(database, name).create_index.assert_called_once()
    assert database.summaries.create_index.call_args.kwargs["unique"] is True


def test_index_failure_is_not_silently_ignored():
    database = MagicMock()
    database.documents.create_index.side_effect = OperationFailure("duplicates or permission")
    with pytest.raises(StorageUnavailable, match="index initialization failed"):
        ensure_indexes(database)


@pytest.mark.parametrize("timeout", [0, -1])
def test_timeout_must_be_positive(timeout):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, mongodb_timeout_ms=timeout)
