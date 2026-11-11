# Background processing (Prompt 12)

## Queue contracts

RabbitMQ carries versioned identity-only messages (job/document IDs, generation,
stage and attempt). Strict validation rejects extra fields and mismatched IDs.
PDF content, source text and provider credentials stay out of queue payloads.
Ingestion, summary and dead-letter queues are durable. Producers use persistent
messages, mandatory routing and publisher confirms. Connection/blocked timeouts
are bounded, and exception responses exclude broker credentials.

Retries are scheduled from a persisted MongoDB job/outbox record. Consumers
acknowledge only after the result or next action is durable. Duplicate
messages are expected with at-least-once delivery; processing must check the
current job identity and reuse existing completed pipeline outputs.

The configured consumer acknowledgement timeout covers long jobs; heartbeats
require processing provider work separately from the RabbitMQ I/O thread.
Queue arguments must match between processes; changing queue arguments requires
a reviewed queue migration instead of deleting existing queues.

References: [RabbitMQ confirms](https://www.rabbitmq.com/docs/confirms),
[RabbitMQ reliability](https://www.rabbitmq.com/docs/reliability),
[Pika threaded consumer example](https://github.com/pika/pika/blob/1.3.2/examples/basic_consumer_threaded.py).


## Upload scheduling and status

A successful upload saves a deterministic `processing_jobs` record in MongoDB
before returning. Duplicate uploads reuse the job. Already-ready PDFs do not
start paid work again. The HTTP request does not connect to RabbitMQ or invoke
providers. If saving the job fails after the PDF was stored, the request fails
safely and retrying the same upload repairs scheduling without duplicating PDF
storage. A reconciliation pass repairs explicitly requested pending uploads;
unrequested legacy files are left alone.

The dispatcher publishes due outbox actions with confirms and then conditionally
marks that exact generation/stage/attempt as sent. A failed/uncertain publish
leaves the action pending. Duplicate delivery is expected. A fast consumer cannot
have its next action overwritten by a delayed publication update.

- GET `/api/v1/documents/{id}/processing` returns safe job status, stage, attempt,
  next retry time and a bounded error code; worker tokens stay private.
- POST `/api/v1/documents/{id}/processing/retry` explicitly restarts a terminal
  failure with a new generation. Old messages cannot identify the new attempt.
  Interrupted work requires operator review and is not reset by this endpoint.
- Retry delays and terminal dead-letter actions are persisted in MongoDB, so no
  RabbitMQ TTL plugin is required and a broker outage cannot erase the schedule.

Increment 12.2 verification: **353 backend tests passed, 4 optional live checks
skipped** with disposable local MongoDB. Provider/publication boundaries were
mocked; worker execution and real-broker checks follow next.


## Workers and failure handling

`python -m backend.services.jobs.main run` starts the dispatcher and separate
consumers for ingestion and summary. Each consumer uses prefetch 1, manual
acknowledgements and a separate provider-work thread so RabbitMQ I/O continues
while parsing or summarizing. Acknowledgement follows saved job completion,
next-stage scheduling, retry scheduling or terminal failure. Persistence failures
leave the delivery unacknowledged. Shutdown waits for in-flight work.

The ingestion worker reuses `parse_pdf`, Markdown chunking and Voyage embedding
storage, then schedules summary. The summary worker validates the same parse,
chunk and embedding generation, reuses the existing LangGraph service and marks
the job complete only with a ready document. Duplicate, early and stale messages
do not invoke providers. Job failures use bounded exponential backoff, then a
durable dead-letter action; raw provider errors never enter the public status.

A MongoDB lease/heartbeat prevents concurrent job owners from advancing the same
job. An expired lease is marked `WORKER_INTERRUPTED` and sent to the dead-letter
queue for review. Existing service claims deliberately do not expire silently:
a hard-killed parser/model request may still be running remotely. This system
provides at-least-once delivery and output reuse, not exactly-once provider billing.

After confirming the old workers have stopped and inspecting the interrupted job,
an operator may run:

```bash
python -m backend.services.jobs.main recover DOCUMENT_ID --confirm-workers-stopped
```

Recovery conditionally clears only the interrupted document's still-running
claims with the matching ownership token. Completed parses, chunks, vectors and
summaries remain stored. A new job generation resumes ingestion and reuses these
outputs. `SOURCE_BUSY` from unrelated/manual processing requires separate review
and is never reset automatically. Normal terminal failures can use the explicit
HTTP retry endpoint; it also starts ingestion with output reuse.

Increment 12.3 verification: **363 backend tests passed, 4 optional live checks
skipped** with disposable MongoDB. Full processing used simulated providers.
Atomic claims, duplicate/early deliveries, bounded retries, changed generations,
reviewed interrupted recovery and acknowledgement-after-persistence passed.


## Run locally

From the repository root, activate the backend environment, install the declared
backend requirements, and populate the ignored `.env`. Keep MongoDB pointed at
Atlas when you need Atlas vector/BM25 retrieval; the local Compose MongoDB service
does not provide Atlas search.

```bash
docker compose up -d rabbitmq
python -m backend.services.jobs.main run
```

Keep the gateway and Vite running in their separate terminals. `run` starts three
threads with independent broker connections: dispatcher, ingestion consumer and
summary consumer. For separate deployments, use `dispatch`, `work ingestion` and
`work summary` instead. Stop with Ctrl+C/SIGTERM; shutdown drains in-flight work.
Broker connection failures retry at the configured poll interval and leave
pending jobs saved. Do not run the operator recovery command against live workers.

The RabbitMQ AMQP and management ports are bound to loopback. Broker queue names,
acknowledgement timeout and credentials must match between processes. Queue
arguments are immutable: inspect an incompatible pre-existing queue and plan a
migration; do not delete it automatically. Changing settings while a job is in
flight can invalidate its source/profile checks; retry explicitly afterward.

The upload screen polls processing and document status, shows the current step
or automatic retry, and enables **Open workspace** only after readiness is
confirmed. A failed job has an explicit retry button; interrupted work asks for
review. A temporary status error preserves the original PDF and does not invent
success. Reconciliation marks repaired scheduling requests so existing jobs cannot
occupy every reconciliation batch indefinitely.

## Deterministic real-broker verification

Use an isolated local MongoDB and disposable RabbitMQ queues, never a production
broker/database, then run:

```bash
RESEARCHAI_TEST_MONGODB_URI='mongodb://127.0.0.1:27017' \
RESEARCHAI_TEST_RABBITMQ_URL='amqp://guest:guest@127.0.0.1:5672/' \
python -m pytest backend/tests/test_job_broker_integration.py -q
```

Tests create random queue/database names and remove only their own resources.
Real HTTP upload, MongoDB/GridFS, RabbitMQ confirms, consumers, retry scheduling,
summary publication and readiness are exercised. Paid provider boundaries are
simulated. Checks cover a transient embedding failure, cache reuse, duplicate
messages, sanitized poison messages, terminal dead-letter publication and an
explicit retry that resumes completed stages.

Final backend verification with real RabbitMQ and disposable MongoDB: **366 tests
passed, 4 optional live provider checks skipped**. Frontend checks include progress,
automatic retry, reviewed interruption, request failures and confirmed workspace
readiness. Production build passed with the existing PDF.js eval/bundle warnings.
No Ragas scores were produced or claimed by this stage.

Isolated staged-copy verification: **75 frontend tests passed** and production
build passed. The local dashboard redesign remains outside this feature commit.


## Local runtime check — 2026-11-12

After verification, the project's persistent Compose RabbitMQ service was started
and the gateway was reloaded. The ingestion and summary queues each had one
connected consumer, with zero ready/unacknowledged messages. Both broker ports
were confirmed bound to `127.0.0.1`. The configured Atlas connection and an
existing document metadata HTTP read succeeded. The new processing/status retry
routes were present in the running API. The frontend remained available on its
existing development port.

The background supervisor was left running for new uploads. Existing unrequested
legacy documents were not scheduled, and no live paid end-to-end provider check
was performed in this stage. Real queue processing was verified by the isolated
integration tests described above. Provider keys and local runtime logs remain
outside version control.
