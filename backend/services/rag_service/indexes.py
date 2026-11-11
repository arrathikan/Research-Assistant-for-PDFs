"""Explicit Atlas vector/BM25 indexes; never overwrite an existing definition."""

import argparse
import json
import sys
from typing import Any

from backend.services.rag_service.models import RagUnavailable
from backend.shared.config import Settings, get_settings
from backend.shared.database import connect_database
from backend.shared.logging import setup_logger
from pymongo.database import Database
from pymongo.errors import PyMongoError
from pymongo.operations import SearchIndexModel


def definitions(settings: Settings) -> list[dict[str, Any]]:
    fields = ["document_id", "chunk_set_id", "embedding_profile_id"]
    return [
        {
            "name": settings.vector_search_index_name,
            "type": "vectorSearch",
            "definition": {
                "fields": [
                    {
                        "type": "vector",
                        "path": "embedding",
                        "numDimensions": settings.voyage_dimensions,
                        "similarity": "cosine",
                    }
                ]
                + [{"type": "filter", "path": field} for field in fields]
            },
        },
        {
            "name": settings.keyword_search_index_name,
            "type": "search",
            "definition": {
                "mappings": {
                    "dynamic": False,
                    "fields": {
                        **{field: {"type": "token"} for field in fields},
                        "chunk": {
                            "type": "document",
                            "dynamic": False,
                            "fields": {
                                "content": {
                                    "type": "string",
                                    "analyzer": "lucene.standard",
                                    "similarity": {"type": "bm25"},
                                }
                            },
                        },
                    },
                }
            },
        },
    ]


def _contains(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and _contains(actual[key], value) for key, value in expected.items()
        )
    if isinstance(expected, list):
        return isinstance(actual, list) and all(
            any(_contains(item, wanted) for item in actual) for wanted in expected
        )
    return actual == expected


def check_indexes(database: Database, settings: Settings, create: bool = False) -> None:
    try:
        for desired in definitions(settings):
            existing = list(database.chunk_embeddings.list_search_indexes(desired["name"]))
            if not existing:
                if create:
                    database.chunk_embeddings.create_search_index(SearchIndexModel(**desired))
                    continue
                raise RagUnavailable(
                    "Atlas search indexes are missing; create the configured indexes first"
                )
            index = existing[0]
            if not _contains(index.get("latestDefinition", {}), desired["definition"]):
                raise RagUnavailable(
                    "Atlas index definition is incompatible; review or choose a new index name"
                )
            if not create and index.get("queryable") is not True:
                raise RagUnavailable("Atlas search index is not queryable yet")
    except PyMongoError:
        raise RagUnavailable(
            "Atlas search index management unavailable; a search-enabled deployment is required"
        ) from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Show Atlas index definitions; --create explicitly creates missing indexes"
    )
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args(argv)
    settings = get_settings()
    if not args.create:
        sys.stdout.write(json.dumps(definitions(settings), indent=2) + "\n")
        return 0
    from backend.shared.database import StorageUnavailable

    try:
        with connect_database(settings) as database:
            check_indexes(database, settings, create=True)
    except (RagUnavailable, StorageUnavailable) as error:
        setup_logger("rag_service").error(str(error))
        return 1
    setup_logger("rag_service").info(
        "Index creation requested/definitions checked; wait until both indexes are queryable"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
