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
