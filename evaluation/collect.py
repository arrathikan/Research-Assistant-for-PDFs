"""Collect isolated single-turn outputs from the application's actual RAG code."""

import hashlib
import json
from time import perf_counter
from uuid import uuid4

from bson import ObjectId
from pymongo.database import Database

from backend.services.rag_service.chain import answer_with_trace
from backend.services.rag_service.models import RagNotReady, RagUnavailable
from backend.services.rag_service.retrieval import current_scope, retrieve_variants
from backend.services.summary_service.workflow import Completion
from backend.shared.config import Settings
from backend.shared.database import StorageUnavailable
from backend.shared.storage import get_document
from evaluation.dataset import BenchmarkDataset, DatasetError
from evaluation.models import CollectedCase, CollectionRun, Strategy


def collect(
    database: Database,
    dataset: BenchmarkDataset,
    bindings: dict[str, str],
    settings: Settings,
    git_commit: str,
    limit: int = 20,
    strategies: tuple[Strategy, ...] = ("hybrid", "semantic"),
    sample_ids: list[str] | None = None,
    complete: Completion | None = None,
) -> CollectionRun:
    if (
        not 1 <= limit <= 100
        or not strategies
        or len(set(strategies)) != len(strategies)
    ):
        raise DatasetError("Invalid evaluation size or strategies")
    cases = [
        case
        for case in dataset.cases
        if sample_ids is None or case.sample_id in sample_ids
    ]
    if (
        not cases
        or sample_ids is not None
        and set(sample_ids) != {case.sample_id for case in cases}
    ):
        raise DatasetError("Selected benchmark cases do not exist")
    cases = cases[:limit]
    scopes = {}
    # Validate every source before the first paid question embedding or model call.
    for key in {case.document_key for case in cases}:
        identifier = bindings.get(key, "")
        if not ObjectId.is_valid(identifier) or identifier != identifier.lower():
            raise DatasetError(
                "Bind benchmark document keys to actual MongoDB document IDs"
            )
        document = get_document(database, identifier)
        source = dataset.sources[key]
        if (
            document is None
            or document.sha256 != source.pdf_sha256
            or document.page_count != source.page_count
        ):
            raise DatasetError("Bound document does not match the exact benchmark PDF")
        scopes[key], _ = current_scope(database, identifier, settings)
    records = []
    for case in cases:
        key, scope = case.document_key, scopes[case.document_key]
        review = next(
            (item for item in dataset.reviews if item.sample_id == case.sample_id), None
        )
        started = perf_counter()
        try:
            current, variants = retrieve_variants(
                database, scope.document_id, case.user_question, settings
            )
            if current != scope:
                raise DatasetError("Source changed")
        except (RagNotReady, RagUnavailable, StorageUnavailable, DatasetError):
            elapsed = (perf_counter() - started) * 1000
            records.extend(
                CollectedCase(
                    case=case,
                    strategy=strategy,
                    review=review,
                    error_code="retrieval_failed",
                    shared_retrieval_ms=elapsed,
                )
                for strategy in strategies
            )
            continue
        elapsed = (perf_counter() - started) * 1000
        for strategy in strategies:
            try:
                output = answer_with_trace(
                    case.user_question,
                    scope,
                    variants[strategy],
                    settings,
                    uuid4().hex,
                    uuid4().hex,
                    complete=complete,
                )
                after, _ = current_scope(database, scope.document_id, settings)
                if after != scope:
                    records.append(
                        CollectedCase(
                            case=case,
                            strategy=strategy,
                            review=review,
                            error_code="source_changed",
                            shared_retrieval_ms=elapsed,
                        )
                    )
                    continue
                output.trace.configuration.update(
                    {
                        "retrieval": strategy,
                        "shared_retrieval_ms": elapsed,
                        "evaluation_history": "single_turn_no_chat_storage",
                    }
                )
                records.append(
                    CollectedCase(
                        case=case,
                        strategy=strategy,
                        review=review,
                        output=output,
                        shared_retrieval_ms=elapsed,
                    )
                )
            except (RagNotReady, RagUnavailable, StorageUnavailable, DatasetError):
                records.append(
                    CollectedCase(
                        case=case,
                        strategy=strategy,
                        review=review,
                        error_code="generation_failed",
                        shared_retrieval_ms=elapsed,
                    )
                )
    canonical = json.dumps(
        dataset.model_dump(mode="json"),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return CollectionRun(
        dataset_id=dataset.dataset_id,
        dataset_version=dataset.version,
        dataset_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
        git_commit=git_commit,
        source_scopes=scopes,
        records=records,
    )
