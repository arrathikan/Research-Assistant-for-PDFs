"""Explicit offline CLI: validate, collect actual outputs, score, and export review templates."""

import argparse
import importlib.metadata
import json
import os
import subprocess
from pathlib import Path

from pydantic import ValidationError

from backend.services.rag_service.models import RagNotReady, RagUnavailable
from backend.shared.config import get_settings
from backend.shared.database import StorageUnavailable, connect_database
from backend.shared.logging import setup_logger
from evaluation.collect import collect
from evaluation.dataset import DatasetError, load_dataset, verify_pdf
from evaluation.judge import JudgeError
from evaluation.metrics import RagasRunner, score_record
from evaluation.models import CollectionRun
from evaluation.report import (
    CRITERIA,
    EvaluationReport,
    ManualAssessment,
    ScoredCase,
    attach_manual_reviews,
    deterministic_checks,
    result_hash,
    write_report,
)
from evaluation.settings import EvaluationSettings

DEFAULT_DATASET = Path(__file__).parent / "datasets/rag_test_cases.json"
DEFAULT_OUTPUT = Path(__file__).parent / "results"


def save_collection(run: CollectionRun, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"collection-{run.run_id}.json"
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(
            run.model_dump(mode="json"),
            stream,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
    return path


def evaluate_collection(
    run: CollectionRun,
    runner: RagasRunner,
    config: EvaluationSettings,
    manual: dict[str, ManualAssessment] | None = None,
) -> EvaluationReport:
    logger = setup_logger("evaluation")
    rows = []
    for index, record in enumerate(run.records, 1):
        scores = score_record(record, runner)
        review = (manual or {}).get(record.case.sample_id + ":" + record.strategy)
        rows.append(
            ScoredCase(
                sample_id=record.case.sample_id,
                strategy=record.strategy,
                metrics=scores,
                checks=deterministic_checks(record),
                manual=review,
            )
        )
        logger.info(f"Scored record {index}/{len(run.records)}")
    metadata = {
        **config.model_dump(),
        "ragas_version": importlib.metadata.version("ragas"),
        "completion_gateway": "OpenRouter",
        "temperature_effective": None
        if config.judge_model.startswith("openai/gpt-5")
        else config.temperature,
        "relevancy_embeddings": "Voyage query embeddings",
    }
    return EvaluationReport(
        collection=run,
        evaluator=metadata,
        request_usage=runner.budget.snapshot(),
        status="partial"
        if any(
            metric.status == "error" for row in rows for metric in row.metrics.values()
        )
        else "complete",
        rows=rows,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline ResearchAI Ragas evaluation; never runs in normal chat"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    validate.add_argument("--pdf", type=Path)
    validate.add_argument("--document-key", default="lost-in-middle-tacl-2024")
    validate.add_argument("--allow-unreviewed", action="store_true")
    for command in ("collect", "run"):
        item = commands.add_parser(command)
        item.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
        item.add_argument("--bindings", type=Path, required=True)
        item.add_argument("--limit", type=int, default=20)
        item.add_argument("--sample-id", action="append")
        item.add_argument(
            "--history",
            type=Path,
            help="Optional reviewed seed question/answer history by sample ID",
        )
        item.add_argument("--strategy", choices=("hybrid", "semantic"), action="append")
        item.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
        item.add_argument("--allow-unreviewed", action="store_true")
        item.add_argument("--live", action="store_true", required=True)
    score = commands.add_parser("score")
    score.add_argument("--collection", type=Path, required=True)
    score.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    score.add_argument("--manual", type=Path)
    score.add_argument("--live", action="store_true", required=True)
    review = commands.add_parser("review")
    review.add_argument("--report", type=Path, required=True)
    review.add_argument("--manual", type=Path, required=True)
    review.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    manual = commands.add_parser("manual-template")
    manual.add_argument("--collection", type=Path, required=True)
    manual.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    logger = setup_logger("evaluation")
    try:
        if args.command == "validate":
            dataset = load_dataset(
                args.dataset, require_reviewed=not args.allow_unreviewed
            )
            if args.pdf:
                verify_pdf(dataset, args.document_key, args.pdf.read_bytes())
            logger.info(
                f"Validated {len(dataset.cases)} benchmark cases; review provenance retained"
            )
            return 0
        if args.command == "manual-template":
            run = CollectionRun.model_validate_json(args.collection.read_text())
            template = {
                record.case.sample_id + ":" + record.strategy: ManualAssessment(
                    result_sha256=result_hash(record),
                    outcomes={key: "pending" for key in CRITERIA},
                ).model_dump(mode="json")
                for record in run.records
            }
            with args.output.open("x") as stream:
                json.dump(template, stream, indent=2)
            logger.info("Created pending manual-review template")
            return 0
        if args.command == "review":
            previous = EvaluationReport.model_validate_json(args.report.read_text())
            reviews = {
                key: ManualAssessment.model_validate(value)
                for key, value in json.loads(args.manual.read_text()).items()
            }
            report = attach_manual_reviews(previous, reviews)
            path, md = write_report(report, args.output)
            logger.info(f"Saved reviewed report without provider calls: {path}; {md}")
            return 0
        config, settings = EvaluationSettings(), get_settings()
        if args.command in ("collect", "run"):
            if not 1 <= args.limit <= config.max_samples:
                raise DatasetError(
                    "Requested sample count exceeds the configured evaluation limit"
                )
            dataset = load_dataset(
                args.dataset, require_reviewed=not args.allow_unreviewed
            )
            bindings = json.loads(args.bindings.read_text())
            if not isinstance(bindings, dict) or not all(
                isinstance(value, str) for value in bindings.values()
            ):
                raise DatasetError(
                    "Document bindings must be a dictionary of database IDs"
                )
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip()
            with connect_database(settings) as database:
                run = collect(
                    database,
                    dataset,
                    bindings,
                    settings,
                    commit,
                    limit=args.limit,
                    strategies=tuple(args.strategy or ("hybrid", "semantic")),
                    sample_ids=args.sample_id,
                    history_by_sample=json.loads(args.history.read_text())
                    if args.history
                    else None,
                )
            path = save_collection(run, args.output)
            logger.info(f"Saved real pipeline collection: {path}")
            if args.command == "collect":
                return 0
        else:
            run = CollectionRun.model_validate_json(args.collection.read_text())
        reviews = (
            {
                key: ManualAssessment.model_validate(value)
                for key, value in json.loads(args.manual.read_text()).items()
            }
            if args.command == "score" and args.manual
            else {}
        )
        os.environ["RAGAS_DO_NOT_TRACK"] = "true"
        runner = RagasRunner(settings, config)
        try:
            report = evaluate_collection(run, runner, config, reviews)
        finally:
            runner.close()
        path, md = write_report(report, args.output)
        logger.info(f"Saved {report.status} evaluation report: {path}; {md}")
        return 0 if report.status == "complete" else 2
    except (
        DatasetError,
        RagNotReady,
        RagUnavailable,
        ImportError,
        JudgeError,
        StorageUnavailable,
        ValidationError,
        OSError,
        ValueError,
        KeyError,
    ):
        logger.error(
            "Evaluation could not complete; check source bindings, readiness, configuration and artifact validation. No missing scores were filled in."
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
