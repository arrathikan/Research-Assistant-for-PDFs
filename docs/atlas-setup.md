# Set up MongoDB Atlas for ResearchAI

## 1. Create a development cluster

Open [MongoDB Atlas](https://cloud.mongodb.com/) and sign in or register. Create a
project named ResearchAI. Create a cluster and select **Free / M0**. Name it
researchai and choose a nearby region available on the free plan. Wait for it to
be ready. [Official cluster guide](https://www.mongodb.com/docs/atlas/tutorial/deploy-free-tier-cluster/).

## 2. Create a database user

In Security / Database Access (or the Security Quickstart), create a password-based
database user, for example `researchai_app`. Grant read/write access to the
`research_assistant` database. Keep the generated password in your password manager.
The database username/password are separate from your Atlas website login.
[Official database-user guide](https://www.mongodb.com/docs/atlas/security-add-mongodb-users/).

The optional test suite creates uniquely named researchai_test databases, so a
user restricted only to research_assistant cannot run that suite. Use a separate,
restricted-to-your-development-cluster test user with the needed test-database
permissions when running it. Do not grant broader permissions to a production user.

## 3. Allow your Mac to connect

In Security / Network Access, add your current public IP address. If your network
or public IP changes later, update this entry.
[Official network guide](https://www.mongodb.com/docs/atlas/security/ip-access-list/).

## 4. Copy the Python connection string

On the cluster, click Connect, choose Drivers and select Python. Copy the generated
`mongodb+srv://...` URI. Replace its username/password placeholders with the
**database user's** values; percent-encode special characters in credentials.
[Official connection guide](https://www.mongodb.com/docs/atlas/driver-connection/).

## 5. Update only the local environment

Edit `.env` in the project root, preserving your other keys:

```dotenv
MONGODB_URI=mongodb+srv://researchai_app:ENCODED_PASSWORD@YOUR_CLUSTER_HOST/?retryWrites=true&w=majority
MONGODB_DB_NAME=research_assistant
```

Use the host/options provided by Atlas. The line above is a placeholder, not a
working URI. Never paste the actual URI into chat or commit it. The project
already ignores `.env`. Existing local PDFs are not automatically copied to Atlas.

## 6. Initialize storage and search

From the repository root with backend dependencies installed and `.env` saved:

```bash
python -m backend.shared.database
```

A new database also needs the empty `chunk_embeddings` collection before search
index creation. The index CLI does not create a missing collection: an empty
namespace can return MongoDB error code 26. Create it in Atlas Collections, or use
this idempotent explicit initialization:

```bash
python - <<'PYCODE'
from backend.shared.config import get_settings
from backend.shared.database import connect_database

with connect_database(get_settings()) as database:
    if "chunk_embeddings" not in database.list_collection_names():
        database.create_collection("chunk_embeddings")
PYCODE
python -m backend.services.rag_service.indexes --create
```

The CLI requests missing vector/BM25 indexes and checks existing definitions without
replacing them. It does not wait for readiness. In Atlas Search, wait for both
`chunk_embeddings_v1` and `chunk_keywords_v1` to be queryable before chat. Running
the module without `--create` only prints index definitions, not live status.

Start the gateway and workers as described in [the README](../README.md); restart
both after environment changes. Upload a PDF and allow actual parsing, chunking,
embedding and summary jobs to finish. Ready document metadata is separate from
search-index readiness and model access.

The optional live test uses a short `researchai_test` database name because the
previously tested cloud deployment enforced a 38-byte name limit. Fresh test
databases may also exceed a shared tier's search-index quota; use dedicated test
infrastructure instead of deleting application indexes. Historical cloud evidence
is in [Atlas verification](atlas-verification.md); current smoke scope is in
[the submission review](submission-review.md).
