"""Storage unit tests with explicit mocked driver failures, not a live database."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from unittest.mock import MagicMock, patch

import pytest
from backend.shared.database import StorageUnavailable
from backend.shared.storage import (
    DocumentNotFound,
    StoredDocument,
    find_document_by_hash,
    get_document,
    read_pdf,
    store_pdf,
)
from bson import ObjectId
from gridfs import NoFile
from pydantic import ValidationError
from pymongo.errors import AutoReconnect, DuplicateKeyError, OperationFailure

PDF = b"%PDF-1.7\nunit test bytes"
DIGEST = sha256(PDF).hexdigest()


def record():
    return {
        "_id": ObjectId(),
        "gridfs_file_id": ObjectId(),
        "sha256": DIGEST,
        "filename": "paper.pdf",
        "file_size_bytes": len(PDF),
    }


def test_stores_bytes_and_validated_metadata():
    database = MagicMock()
    database.documents.find_one.return_value = None
    with patch("backend.shared.storage.GridFSBucket") as constructor:
        result = store_pdf(database, "paper.pdf", PDF)
        stored = database.documents.insert_one.call_args.args[0]
        assert isinstance(stored["_id"], ObjectId)
        assert isinstance(stored["gridfs_file_id"], ObjectId)
        assert stored["sha256"] == DIGEST
        assert result.document.id == str(stored["_id"])
        assert result.document.status == "PENDING"
        assert result.document.created_at.tzinfo is not None
        assert result.document.created_at.microsecond % 1000 == 0
        assert result.document.updated_at.microsecond % 1000 == 0
        assert result.is_duplicate is False
        args = constructor.return_value.upload_from_stream_with_id.call_args
        assert args.args == (stored["gridfs_file_id"], "paper.pdf", PDF)
        assert args.kwargs["metadata"]["document_id"] == result.document.id


def test_existing_duplicate_does_not_write_a_file():
    database = MagicMock()
    existing = record()
    database.documents.find_one.return_value = existing
    with patch("backend.shared.storage.GridFSBucket") as constructor:
        result = store_pdf(database, "renamed.pdf", PDF)
    assert result.is_duplicate is True
    assert result.document.id == str(existing["_id"])
    constructor.assert_not_called()
    database.documents.insert_one.assert_not_called()


def test_concurrent_duplicate_deletes_only_losing_file():
    database = MagicMock()
    existing = record()
    database.documents.find_one.side_effect = [None, existing]
    database.documents.insert_one.side_effect = DuplicateKeyError("sha256 race")
    with patch("backend.shared.storage.GridFSBucket") as constructor:
        result = store_pdf(database, "paper.pdf", PDF)
        bucket = constructor.return_value
        candidate = bucket.upload_from_stream_with_id.call_args.args[0]
        bucket.delete.assert_called_once_with(candidate)
    assert candidate != existing["gridfs_file_id"]
    assert result.is_duplicate is True
    assert result.document.id == str(existing["_id"])


def test_failed_upload_cleans_its_candidate():
    database = MagicMock()
    database.documents.find_one.return_value = None
    with patch("backend.shared.storage.GridFSBucket") as constructor:
        bucket = constructor.return_value
        bucket.upload_from_stream_with_id.side_effect = AutoReconnect("private-uri")
        with pytest.raises(StorageUnavailable, match="^PDF storage unavailable$"):
            store_pdf(database, "paper.pdf", PDF)
        bucket.delete.assert_called_once_with(bucket.upload_from_stream_with_id.call_args.args[0])
    database.documents.insert_one.assert_not_called()


def test_ambiguous_insert_keeps_file_to_avoid_corrupting_committed_record():
    database = MagicMock()
    database.documents.find_one.return_value = None
    database.documents.insert_one.side_effect = AutoReconnect("private-uri")
    with patch("backend.shared.storage.GridFSBucket") as constructor:
        with pytest.raises(StorageUnavailable, match="persistence uncertain"):
            store_pdf(database, "paper.pdf", PDF)
        constructor.return_value.delete.assert_not_called()


def test_duplicate_cleanup_failure_is_reported():
    database = MagicMock()
    database.documents.find_one.return_value = None
    database.documents.insert_one.side_effect = DuplicateKeyError("race")
    with patch("backend.shared.storage.GridFSBucket") as constructor:
        constructor.return_value.delete.side_effect = OperationFailure("private")
        with pytest.raises(StorageUnavailable, match="cleanup failed"):
            store_pdf(database, "paper.pdf", PDF)


def test_disappearing_duplicate_is_reported():
    database = MagicMock()
    database.documents.find_one.return_value = None
    database.documents.insert_one.side_effect = DuplicateKeyError("race")
    with patch("backend.shared.storage.GridFSBucket"):
        with pytest.raises(StorageUnavailable, match="Duplicate document unavailable"):
            store_pdf(database, "paper.pdf", PDF)


def test_no_file_during_cleanup_is_safe():
    database = MagicMock()
    database.documents.find_one.side_effect = [None, record()]
    database.documents.insert_one.side_effect = DuplicateKeyError("race")
    with patch("backend.shared.storage.GridFSBucket") as constructor:
        constructor.return_value.delete.side_effect = NoFile("already absent")
        assert store_pdf(database, "paper.pdf", PDF).is_duplicate


def test_lookup_by_id_and_hash_converts_bson_ids():
    database = MagicMock()
    existing = record()
    database.documents.find_one.return_value = existing
    assert get_document(database, str(existing["_id"])).id == str(existing["_id"])
    database.documents.find_one.assert_called_with({"_id": existing["_id"]})
    assert find_document_by_hash(database, DIGEST).gridfs_file_id == str(existing["gridfs_file_id"])
    database.documents.find_one.assert_called_with({"sha256": DIGEST})


def test_absent_metadata_returns_none():
    database = MagicMock()
    database.documents.find_one.return_value = None
    assert get_document(database, str(ObjectId())) is None
    assert find_document_by_hash(database, DIGEST) is None


@pytest.mark.parametrize(
    "operation",
    [lambda db: get_document(db, str(ObjectId())), lambda db: find_document_by_hash(db, DIGEST)],
)
def test_lookup_failure_hides_driver_message(operation):
    database = MagicMock()
    database.documents.find_one.side_effect = AutoReconnect("private-uri")
    with pytest.raises(StorageUnavailable, match="^Document lookup unavailable$"):
        operation(database)


def test_invalid_identifiers_are_rejected_before_database_access():
    database = MagicMock()
    with pytest.raises(ValueError):
        get_document(database, "invalid-id")
    with pytest.raises(ValueError):
        find_document_by_hash(database, "not-a-digest")
    database.documents.find_one.assert_not_called()


@pytest.mark.parametrize(
    "field,value", [("sha256", "bad"), ("file_size_bytes", 0), ("filename", ""), ("page_count", 0)]
)
def test_metadata_validation(field, value):
    data = record()
    data["_id"] = str(data["_id"])
    data["gridfs_file_id"] = str(data["gridfs_file_id"])
    data[field] = value
    with pytest.raises(ValidationError):
        StoredDocument.model_validate(data)


def test_empty_content_rejected_before_database_access():
    database = MagicMock()
    with pytest.raises(ValidationError):
        store_pdf(database, "paper.pdf", b"")
    database.documents.find_one.assert_not_called()


def test_file_retrieved_by_id_and_stream_closed():
    database = MagicMock()
    existing = record()
    database.documents.find_one.return_value = existing
    with patch("backend.shared.storage.GridFSBucket") as constructor:
        stream = constructor.return_value.open_download_stream.return_value
        stream.__enter__.return_value.read.return_value = PDF
        assert read_pdf(database, str(existing["_id"])) == PDF
        constructor.return_value.open_download_stream.assert_called_once_with(
            existing["gridfs_file_id"]
        )
        stream.__exit__.assert_called_once()


@pytest.mark.parametrize(
    "failure,expected",
    [(NoFile("private"), DocumentNotFound), (AutoReconnect("private"), StorageUnavailable)],
)
def test_download_failures(failure, expected):
    database = MagicMock()
    existing = record()
    database.documents.find_one.return_value = existing
    with patch("backend.shared.storage.GridFSBucket") as constructor:
        constructor.return_value.open_download_stream.side_effect = failure
        with pytest.raises(expected):
            read_pdf(database, str(existing["_id"]))


def test_download_of_missing_document():
    database = MagicMock()
    database.documents.find_one.return_value = None
    with pytest.raises(DocumentNotFound):
        read_pdf(database, str(ObjectId()))


def test_storage_timestamps_match_bson_millisecond_precision():
    data = record()
    data["_id"] = str(data["_id"])
    data["gridfs_file_id"] = str(data["gridfs_file_id"])
    data["created_at"] = datetime(
        2026, 11, 10, 12, 0, 0, 123456, tzinfo=timezone(timedelta(hours=5, minutes=30))
    )
    data["updated_at"] = datetime(2026, 11, 10, 7, 0, 0, 987654)
    document = StoredDocument.model_validate(data)
    assert document.created_at == datetime(2026, 11, 10, 6, 30, 0, 123000, tzinfo=timezone.utc)
    assert document.updated_at == datetime(2026, 11, 10, 7, 0, 0, 987000, tzinfo=timezone.utc)
