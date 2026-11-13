# Continuous integration

[GitHub Actions runs](https://github.com/arrathikan/Research-Assistant-for-PDFs/actions/workflows/ci.yml)
are the authoritative remote status. The workflow runs on pushes to `main` and
`codex/**`, pull requests targeting `main`, and manual dispatch.

## Checks

| Job | Checks |
| --- | --- |
| Backend tests and lint | Python 3.12, Ruff, unit tests and real disposable MongoDB/RabbitMQ integration tests |
| Frontend tests and build | Node 22, lockfile-based `npm ci`, Vitest, strict TypeScript and the Vite production build |
| Docker build and full-stack smoke | Both serving images, health/non-root checks, static/PDF assets and proxied storage lifecycle |

Container checks run after backend/frontend checks succeed. Each job has a timeout;
a newer run cancels an older run on the same ref. Official checkout/setup actions
are pinned to verified full commit SHAs. Checkout does not persist its Git credential,
and workflow permissions are restricted to repository-content reads. No images
are published, no application is deployed and no PR is merged by this workflow.

## No paid provider calls

Normal CI receives **no provider or Atlas secrets**. Backend integration fixtures
create unique databases and queues in ephemeral MongoDB/RabbitMQ service containers,
then delete only their own resources. Paid boundaries are simulated in deterministic
integration tests. The four opt-in paid tests are excluded by their existing markers:

```bash
python -m pytest backend/tests -m 'not live_parser and not live_rag and not live_summary' -q
```

Offline Ragas dependencies are installed in the test environment because deterministic
metric/schema/report tests import them. A real judge evaluation is not run. The
serving Docker image excludes Ragas, pytest and Ruff. Run actual Ragas benchmarks
separately using [the evaluation guide](../evaluation/README.md), with explicit
credentials, budgets and honest recorded results. CI status is not an accuracy score.

The Compose smoke check supplies empty provider keys and a synthetic local database.
It verifies storage/queue status, not real parsing, live Atlas search or answer
quality. Public/private PDFs, conversations and secrets are not uploaded as artifacts.

## Reproduce locally

From the repository root, in the backend development environment:

```bash
python -m pip install -r backend/requirements.txt -r evaluation/requirements.txt
ruff check backend
ruff check --config backend/pyproject.toml scripts/compose_smoke.py
ruff format --check --config backend/pyproject.toml scripts/compose_smoke.py
RESEARCHAI_TEST_MONGODB_URI=mongodb://127.0.0.1:27017 \
RESEARCHAI_TEST_RABBITMQ_URL=amqp://guest:guest@127.0.0.1:5672/ \
python -m pytest backend/tests -m 'not live_parser and not live_rag and not live_summary' -q
```

The test URIs must point to non-production infrastructure. Fixtures choose random
resource names and never read the application's `.env` as their database target.
Keep the normal Ruff discovery for `backend`; use the explicit backend config only
for the repository-level smoke script, so import classification matches existing code.

```bash
cd frontend
npm ci --no-audit --no-fund
npm test
npm run typecheck
npx playwright install chromium
npm run test:e2e
npm run build
```

There is no standalone frontend lint script configured; no ESLint pass is claimed.
TypeScript includes the existing unused-code and strict type checks. The build still
reports the upstream PDF.js `eval` warning. Node 22 and Python 3.12 are the CI targets;
provider/storage package constraints are preserved rather than replaced with a new
lockfile. Frontend dependencies use the existing committed npm lockfile.

From the repository root with Docker running:

```bash
python scripts/compose_smoke.py
```

This uses random ports and uniquely named test resources. See [deployment](deployment.md)
for startup, environment separation, cleanup, health semantics and runtime limitations.

## Review and maintenance

Review all three jobs before merging. Branch protection is a repository-owner decision;
this increment does not change it. The frontend job also runs 14 deterministic Chromium browser checks without
provider calls. Paid live QA and offline Ragas are explicitly excluded; see
[browser QA](browser-qa.md).
Update pinned action SHAs deliberately after checking official releases. Rebuild and
verify base images when applying security updates. The existing broker version/data
format is retained; broker upgrades require a separate compatibility/data migration.

References: [GitHub service containers](https://docs.github.com/en/actions/tutorials/use-containerized-services/use-docker-service-containers),
[GitHub secure workflow guidance](https://docs.github.com/en/actions/reference/security/secure-use),
[Node workflow setup](https://github.com/actions/setup-node),
[Python workflow setup](https://github.com/actions/setup-python).
