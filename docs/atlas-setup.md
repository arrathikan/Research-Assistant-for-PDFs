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

## 6. Verify and create application indexes

After saving `.env`, restart the gateway to reload its cached settings. From the
project root with backend dependencies installed:

```bash
python -m backend.shared.database
python -m backend.services.rag_service.indexes --create
```

The first command connects and initializes ordinary application collections/indexes.
The second creates missing vector/BM25 search indexes without overwriting existing
ones. Wait until both are queryable. A freshly created database needs actual
uploaded/parsed/chunked/embedded documents before chat can return evidence.

When working with the assistant, reply **Atlas ready** after saving the URI
locally. The assistant can then verify the connection without displaying it and
complete the remaining live search checks. See [hybrid RAG](hybrid-rag.md) for the
explicit optional live-test requirements and current verification scope.
