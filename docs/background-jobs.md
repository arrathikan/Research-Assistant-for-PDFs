# Background processing (Prompt 12)

## Queue contracts

RabbitMQ carries versioned identity-only messages (job/document IDs, generation,
stage and attempt). Strict validation rejects extra fields and mismatched IDs.
PDF content, source text and provider credentials stay out of queue payloads.
Ingestion, summary and dead-letter queues are durable. Producers use persistent
messages, mandatory routing and publisher confirms. Connection/blocked timeouts
are bounded, and exception responses exclude broker credentials.

Retries will be scheduled from a persisted MongoDB job/outbox record. Consumers
must acknowledge only after the result or next action is durable. Duplicate
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
