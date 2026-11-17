# ResearchAI — Background Processing Architecture

ResearchAI uses **RabbitMQ, MongoDB, and Python background workers** to process uploaded research papers asynchronously.

The background processing system handles computationally expensive operations such as PDF extraction, Markdown chunking, embedding generation, and structured summarization without blocking the FastAPI request lifecycle.

Its primary objectives are **reliability, fault tolerance, recoverability, and efficient reuse of completed processing artifacts**.

## 1. System Overview

When a user uploads a PDF, ResearchAI validates and stores the document before creating a durable processing job.

RabbitMQ coordinates the delivery of processing tasks, while independent Python workers execute the document-processing pipeline.

The system uses MongoDB to maintain persistent job state, enabling supported retries and recovery when a worker or message broker fails.

### Architecture

```mermaid
flowchart TD
    A["PDF Upload"] --> B["FastAPI Gateway"]
    B --> C["MongoDB GridFS"]
    B --> D["Persistent Processing Job"]

    D --> E["Outbox Dispatcher"]
    E --> F["RabbitMQ"]

    F --> G["Ingestion Worker"]
    G --> H["LlamaParse Extraction"]
    H --> I["Markdown Chunking"]
    I --> J["Voyage AI Embeddings"]

    J --> K["MongoDB Processing State"]
    K --> L["Summary Job"]

    L --> F
    F --> M["Summary Worker"]
    M --> N["LangGraph Summarization"]
    N --> O["Versioned Summary Storage"]
    O --> P["Document READY"]

    G --> Q["Retry / Dead-Letter Handling"]
    M --> Q
    Q --> K
```

The API gateway, dispatcher, and background workers operate as separate execution components.

---

## 2. Queue Architecture

ResearchAI uses durable RabbitMQ queues for different processing responsibilities.

| Queue | Responsibility |
|---|---|
| Ingestion Queue | Execute document extraction, chunking, and embeddings |
| Summary Queue | Execute LangGraph summary generation |
| Dead-Letter Queue | Preserve failed processing actions for inspection |

RabbitMQ messages contain only the information required to identify a processing task.

### Message Contract

A processing message contains versioned identifiers such as:

- Job ID
- Document ID
- Job generation
- Processing stage
- Attempt number

**PDF content, extracted research text, and API credentials are never included in queue messages.**

Message schemas reject unexpected fields and mismatched identifiers.

### Delivery Reliability

The queue integration uses:

- Durable queues
- Persistent messages
- Publisher confirmations
- Mandatory routing
- Manual consumer acknowledgments
- Bounded connection timeouts
- Explicit message validation

RabbitMQ provides **at-least-once delivery**, meaning duplicate messages are possible.

The application therefore validates job identities and uses idempotent processing mechanisms instead of assuming every message will be delivered exactly once.

---

## 3. Durable Job Scheduling

ResearchAI uses a MongoDB-backed job and outbox mechanism to ensure that processing requests survive temporary broker outages.

### Scheduling Workflow

1. FastAPI validates and stores the uploaded PDF.
2. A persistent processing job is created in MongoDB.
3. The outbox dispatcher identifies pending actions.
4. The dispatcher publishes messages to RabbitMQ.
5. RabbitMQ confirms message publication.
6. The corresponding job action is conditionally marked as published.

The upload request does not directly invoke external AI providers or establish a RabbitMQ publishing connection.

### Duplicate Upload Handling

ResearchAI uses SHA-256-based duplicate detection.

When an identical PDF already exists, the application can reuse the stored document and its existing processing job.

A document that has already completed processing does not automatically repeat paid operations.

If job scheduling fails after document storage, retrying the upload can repair the scheduling state without storing another copy of the same PDF.

---

## 4. Worker Execution

ResearchAI separates document ingestion and summarization into independent processing responsibilities.

### Ingestion Worker

The ingestion worker performs:

1. PDF extraction using LlamaParse
2. Markdown-aware document chunking
3. Voyage AI embedding generation
4. Persistence of completed processing artifacts
5. Scheduling of the summary stage

The worker reuses previously completed artifacts when their source and configuration remain compatible.

### Summary Worker

The summary worker:

1. Validates the current document-processing generation.
2. Loads the processed document chunks.
3. Executes the existing LangGraph summarization workflow.
4. Validates generated summary evidence.
5. Persists the completed summary.
6. Marks the document ready when all required artifacts are available.

The workers execute provider operations separately from the RabbitMQ I/O thread to maintain connection heartbeats during long-running tasks.

Each consumer uses controlled message prefetch and manual acknowledgments.

---

## 5. Message Acknowledgment Strategy

ResearchAI acknowledges RabbitMQ messages only after the corresponding processing result or next action has been durably persisted.

### Successful Execution

```mermaid
sequenceDiagram
    participant Q as RabbitMQ
    participant W as Worker
    participant D as MongoDB

    Q->>W: Deliver job message
    W->>D: Validate and claim job
    W->>W: Execute processing
    W->>D: Persist result and next action
    D-->>W: Persistence confirmed
    W->>Q: Acknowledge message
```

### Processing Failure

When a processing operation fails, the worker records the failure and its next action in MongoDB.

Supported transient failures are retried using bounded exponential backoff.

If the retry limit is reached, the job transitions to a terminal failure state and a durable dead-letter action is scheduled.

If persistence fails, the worker does not acknowledge the message as successfully completed.

This approach reduces the risk of losing job state during worker or broker interruptions.

---

## 6. Retry and Failure Handling

ResearchAI uses persistent retry scheduling rather than relying entirely on RabbitMQ message expiration.

### Retry Mechanisms

| Mechanism | Purpose |
|---|---|
| Exponential Backoff | Delay repeated transient failures |
| Maximum Attempts | Prevent unlimited retries |
| Durable Retry Records | Preserve schedules during broker downtime |
| Dead-Letter Handling | Retain terminal failures for inspection |
| Idempotency Checks | Avoid unnecessary duplicate processing |
| Artifact Reuse | Skip previously completed processing stages |
| Job Generation Validation | Reject outdated or duplicate task messages |

Failed jobs expose safe error information through the API.

Raw provider exceptions and credentials are not returned to users.

### At-Least-Once Processing

A worker may receive a duplicate message if a previous delivery was not acknowledged.

Before performing paid provider operations, the application checks the current job identity, processing generation, and existing completed artifacts.

This reduces duplicate execution, but it does not guarantee exactly-once billing by external providers.

---

## 7. Worker Recovery

ResearchAI uses MongoDB ownership claims, leases, and heartbeats to coordinate worker execution.

These mechanisms help prevent multiple workers from advancing the same job simultaneously.

When a worker is interrupted, the system can mark the job with a `WORKER_INTERRUPTED` state for operator review.

### Manual Recovery

After confirming that the original workers have stopped, an operator can run:

```bash
python -m backend.services.jobs.main recover DOCUMENT_ID --confirm-workers-stopped
```

Replace `DOCUMENT_ID` with the affected document identifier.

The recovery process conditionally clears the matching interrupted processing claims and creates a new job generation.

Previously completed extraction, chunking, embedding, and summary artifacts remain available for reuse.

**Important:** Do not execute manual recovery against active workers. A hard-killed process may have initiated an external provider request that is still running.

Normal terminal failures can use the supported retry API instead.

---

## 8. Processing API

The FastAPI gateway exposes endpoints for monitoring and retrying background jobs.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/documents/{id}/processing` | Retrieve processing status |
| `POST` | `/api/v1/documents/{id}/processing/retry` | Retry a terminal failure |

### Processing Status

The status endpoint provides information such as:

- Current processing stage
- Job status
- Attempt number
- Next scheduled retry
- Safe error code

Internal worker ownership tokens remain private.

### Retry Endpoint

The retry endpoint creates a new processing generation for an eligible terminal failure.

Messages associated with earlier generations cannot advance the new processing attempt.

Interrupted work requiring operator review is not automatically reset by the normal retry endpoint.

---

## 9. Frontend Integration

The React upload interface communicates with the processing API to display document status.

The frontend supports:

- Upload confirmation
- Processing progress
- Current processing stage
- Automatic retry states
- Failed-job notifications
- Manual retry actions
- Confirmed document readiness

The **Open Workspace** action becomes available only when the required document-processing artifacts are ready.

Temporary status failures do not cause the frontend to display fabricated success or discard the original uploaded PDF.

---

## 10. Running Background Workers

### Prerequisites

Ensure that:

- MongoDB is configured.
- RabbitMQ is available.
- Backend dependencies are installed.
- Required provider API keys are configured.
- The Python environment is activated.

### Start RabbitMQ

From the repository root:

```bash
docker compose up -d rabbitmq
```

### Start Background Processing

```bash
python -m backend.services.jobs.main run
```

This starts the dispatcher and consumers for ingestion and summarization.

Keep the FastAPI gateway and React frontend running in separate terminals.

### Run Components Independently

For more granular process management:

**Dispatcher**

```bash
python -m backend.services.jobs.main dispatch
```

**Ingestion Worker**

```bash
python -m backend.services.jobs.main work ingestion
```

**Summary Worker**

```bash
python -m backend.services.jobs.main work summary
```

The combined `run` command is convenient for local development, while separate processes allow more flexible worker deployment.

Stop workers gracefully using `Ctrl+C` or `SIGTERM`.

### Infrastructure Notes

RabbitMQ connection settings and queue arguments must remain consistent across producers and consumers.

Incompatible queue configuration changes require a reviewed migration rather than automatic deletion of existing queues.

MongoDB Atlas is required for the full vector and BM25 retrieval workflow. Standalone local MongoDB is sufficient for supported storage and job-processing tests but does not replace Atlas Search.

---

## 11. Testing and Verification

ResearchAI includes deterministic unit tests and real-broker integration tests for background processing.

### Real-Broker Integration Test

Run against disposable local test infrastructure:

```bash
RESEARCHAI_TEST_MONGODB_URI='mongodb://127.0.0.1:27017' \
RESEARCHAI_TEST_RABBITMQ_URL='amqp://guest:guest@127.0.0.1:5672/' \
python -m pytest backend/tests/test_job_broker_integration.py -q
```

The integration test uses isolated MongoDB databases and RabbitMQ queues.

### Test Coverage

The tests verify:

- Durable job creation and scheduling
- RabbitMQ publisher confirmations
- Message consumption and acknowledgment
- Duplicate and outdated message handling
- Transient processing failures
- Retry scheduling and exponential backoff
- Terminal dead-letter publication
- Recovery from interrupted processing
- Completed artifact reuse
- Document readiness transitions

Paid parsing, embedding, and LLM provider operations are simulated during deterministic broker tests.

### Verified Results

The documented real-broker verification completed successfully with:

| Test Area | Result |
|---|---|
| Backend test suite | 366 passed |
| Optional live provider checks | 4 skipped |
| Frontend tests | 75 passed |
| Frontend production build | Passed |

These results verify the tested background-processing behavior and integration contracts.

They do not establish external provider reliability under production traffic or measure RAG answer accuracy.

For broader project verification, see [Final QA Report](final-qa.md).

---

## 12. Engineering Decisions

| Decision | Rationale |
|---|---|
| RabbitMQ | Separate long-running processing from HTTP requests |
| MongoDB Job Outbox | Preserve scheduling during broker outages |
| Identity-Only Messages | Avoid transferring document content through queues |
| At-Least-Once Delivery | Support reliable message redelivery |
| Manual Acknowledgments | Acknowledge only after durable processing results |
| Idempotent Job Execution | Reduce duplicate processing and provider requests |
| Versioned Job Generations | Reject stale processing messages |
| Persistent Retry Scheduling | Preserve retry state independently of RabbitMQ |
| Dead-Letter Queue | Support inspection of terminal failures |
| Manual Recovery | Avoid unsafe automatic retries of uncertain provider calls |
| Artifact Reuse | Reduce repeated processing cost |

---

## 13. Limitations and Future Improvements

The background processing architecture has several known limitations:

- At-least-once message delivery can produce duplicate messages.
- External provider operations are not guaranteed to execute exactly once.
- Interrupted jobs may require manual operator recovery.
- RabbitMQ and MongoDB add infrastructure and operational complexity.
- Processing duration depends on PDF size and external provider performance.
- Provider rate limits and credit availability can delay or prevent job completion.
- The current design requires further production load testing and operational monitoring.

Future improvements include enhanced worker observability, autoscaling, structured operational dashboards, and broader concurrent-processing benchmarks.

---

## 14. References

- [RabbitMQ Publisher Confirms](https://www.rabbitmq.com/docs/confirms)
- [RabbitMQ Reliability Guide](https://www.rabbitmq.com/docs/reliability)
- [Pika Threaded Consumer Example](https://github.com/pika/pika/blob/1.3.2/examples/basic_consumer_threaded.py)
- [System Architecture](architecture.md)
- [Structured Summarization](structured-summary.md)
- [Hybrid RAG Pipeline](hybrid-rag.md)
- [Deployment Guide](deployment.md)
- [Final QA Report](final-qa.md)

---

**ResearchAI Background Processing — Reliable asynchronous document ingestion, summarization, and recovery.**
