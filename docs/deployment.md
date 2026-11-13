# Docker setup and operations

## Prerequisites

Install Docker Desktop with Compose 2.24+ (or Docker Engine and the Compose plugin).
Copy `.env.example` to the ignored `.env` and configure the existing provider keys.
Never put credentials into Dockerfiles, build arguments, frontend variables or Git.

## Start with the existing Atlas database

With an Atlas `MONGODB_URI` in `.env`, run from the repository root:

```bash
docker compose up -d --build --wait
```

Open <http://localhost:3000>. The frontend serves the built application through
Nginx and proxies `/api/` to the gateway. It uses the same origin for upload, chat,
PDF streams and citations. The gateway, dispatcher and ingestion/summary workers
start with the app; a separate Python terminal is not needed.

Atlas still needs database permissions, network access and the existing vector and
keyword indexes. Follow [Atlas setup](atlas-setup.md) and [hybrid retrieval](hybrid-rag.md).
Docker does not replace Atlas or automatically create cloud search indexes.

If the native gateway already occupies port 8000, use a different published port:

```bash
APP_PORT=18000 FRONTEND_PORT=3000 docker compose up -d --build --wait
```

Do not run a second host worker supervisor against the same queues just to test
Docker. Complete/drain in-flight jobs before switching your normal runtime.

## Optional local storage

Local MongoDB is behind the `local` profile to avoid accidentally replacing Atlas
or colliding with an existing local database. Explicitly use its container hostname:

```bash
MONGODB_URI=mongodb://mongodb:27017 docker compose --profile local up -d --build --wait
```

Local MongoDB supports storage, uploads and deterministic tests. It does **not**
provide Atlas Vector Search/BM25; a successful local startup does not prove live RAG.
Inside containers, `localhost` refers to the container itself. An Atlas URI is
passed through unchanged; a native `mongodb://localhost:27017` URI needs the local
command above or an explicitly reachable host database address.

## Configuration and data

Backend containers read `.env` at runtime only. `RESEARCHAI_ENV_FILE` can select a
different runtime file. Compose uses `rabbitmq` as the internal broker hostname;
`DOCKER_RABBITMQ_URL` overrides it for an external broker or URL-encoded credentials.
Changing credentials on an existing RabbitMQ volume does not recreate its users.

Published ports bind to loopback:

| Setting | Default | Use |
| --- | --- | --- |
| `FRONTEND_PORT` | 3000 | Built app and API proxy |
| `APP_PORT` | 8000 | Direct API and `/docs` |
| `MONGODB_PORT` | 27017 | Local-profile database only |
| `AMQP_PORT` | 5672 | Host workers/broker access |
| `RABBITMQ_MANAGEMENT_PORT` | 15672 | Local broker administration |

Existing named MongoDB/RabbitMQ volumes and the existing network names are retained.
The gateway build produces one non-root Python image that workers reuse; it is
not exported concurrently by two build targets. Tests, Ruff and the optional
Ragas evaluation stack stay outside that serving image. The frontend uses a separate
Node build stage and a non-root Nginx runtime, without Node modules or provider keys.
`VITE_API_BASE_URL=/api/v1` is a public build setting in that image. Native Vite keeps
its existing API URL configuration.

Nginx allows a 26 MiB multipart request envelope; the API and frontend retain the
25 MiB PDF limit. Keep these limits aligned when changing configuration. API proxy
reads allow ten minutes for existing chat calls, not synchronous PDF processing.
The optional PDF fonts/CMaps are copied from the installed PDF.js version.

## Health, logs and shutdown

```bash
docker compose ps
docker compose logs --tail=100 gateway workers
docker compose config -q
```

Use `config -q` for validation: plain `docker compose config` expands runtime
credentials into its output. Gateway health is HTTP liveness, not Atlas/provider
readiness. Worker health checks broker queues for consumers. MongoDB and RabbitMQ
have their own probes; the frontend waits for gateway health. Health checks make
no paid provider or Ragas calls.

```bash
docker compose stop
```

Stop retains containers and persistent data. Workers receive a graceful shutdown
and have up to ten minutes to finish current work. Exceeding that grace period can
leave an interrupted job requiring [reviewed recovery](background-jobs.md). Docker
restarts exited services with `unless-stopped`; an unhealthy probe alone does not
restart a container. Rebuild/recreate the gateway and every worker together after
changing persistence/deletion logic.

This is a local/demo deployment. Authentication, authorization, public TLS and
multi-user operations are not added by Compose. No automatic production deployment,
image publication or merge is part of Prompt 14.

## Disposable full-stack smoke check

```bash
python scripts/compose_smoke.py
```

This builds and starts uniquely named containers, network and volumes with random
loopback ports, a synthetic local database and **empty provider keys**. It checks
health, non-root users, built assets/PDF fonts, the API proxy, multipart upload,
SHA-256 deduplication, original PDF bytes, job status and deletion. It always tears
down only its own resources. Existing application containers, queues, Atlas data,
PDFs and volumes are not selected. The smoke check does not claim live parsing or
RAG quality; existing integration tests simulate paid boundaries separately.

## References

- [Docker multi-stage builds](https://docs.docker.com/build/building/multi-stage/).
- [Compose startup and health dependencies](https://docs.docker.com/compose/how-tos/startup-order/).
- [Compose runtime environment files](https://docs.docker.com/reference/compose-file/services/#env_file).

## Prompt 14.1 verification

The clean-copy frontend suite passed **140 tests**. The backend suite passed **473
tests with 4 paid-provider tests deselected**, using real disposable MongoDB and
RabbitMQ fixtures. Both Dockerfiles passed build checks without warnings, both
images built, and the isolated full-stack smoke passed all assertions. Its test
resources were cleaned up; the existing application runtime and data were preserved.
