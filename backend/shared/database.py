"""Explicit MongoDB connection lifecycle and idempotent collection indexes."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from backend.shared.config import Settings
from pymongo import ASCENDING, MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError


class StorageUnavailable(RuntimeError):
    """Storage failed; the message is safe to return without credentials."""


@contextmanager
def connect_database(settings: Settings) -> Iterator[Database[dict[str, Any]]]:
    """Open a bounded connection; close it even when ping or an operation fails.

    Never log the URI or expose the original driver exception. These synchronous
    helpers belong in workers or FastAPI sync routes, not the async event loop.
    """
    client: MongoClient[dict[str, Any]] | None = None
    try:
        client = MongoClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=settings.mongodb_timeout_ms,
            connectTimeoutMS=settings.mongodb_timeout_ms,
            socketTimeoutMS=settings.mongodb_timeout_ms,
            tz_aware=True,
        )
        client.admin.command("ping")
        yield client[settings.mongodb_db_name]
    except PyMongoError:
        raise StorageUnavailable("MongoDB operation unavailable") from None
    finally:
        if client is not None:
            client.close()


def ensure_indexes(database: Database[dict[str, Any]]) -> None:
    """Create all six domain collections through their lookup indexes.

    MongoDB's default _id index is the document identifier uniqueness constraint.
    SHA-256 uniqueness is enforced by MongoDB, never by a check-then-insert alone.
    Existing duplicate data makes initialization fail rather than deleting data.
    GridFS manages its own fs.files/fs.chunks indexes on the first upload.
    """
    try:
        database.documents.create_index("sha256", unique=True, name="unique_sha256")
        database.documents.create_index("created_at", name="documents_created_at")
        database.chunks.create_index(
            [("document_id", ASCENDING), ("chunk_index", ASCENDING)],
            unique=True,
            name="document_chunk_index",
        )
        database.source_elements.create_index(
            [("document_id", ASCENDING), ("page_number", ASCENDING)],
            name="document_source_pages",
        )
        database.summaries.create_index("document_id", unique=True, name="document_summary")
        database.chat_messages.create_index(
            [("document_id", ASCENDING), ("created_at", ASCENDING)],
            name="document_chat_history",
        )
        database.processing_jobs.create_index(
            [("document_id", ASCENDING), ("created_at", ASCENDING)],
            name="document_jobs",
        )
    except PyMongoError:
        raise StorageUnavailable("MongoDB index initialization failed") from None


def main() -> None:
    """Initialize the configured database explicitly, without starting the API."""
    from backend.shared.config import get_settings
    from backend.shared.logging import setup_logger

    with connect_database(get_settings()) as database:
        ensure_indexes(database)
    setup_logger("storage").info("MongoDB collections and indexes initialized")


if __name__ == "__main__":
    main()
