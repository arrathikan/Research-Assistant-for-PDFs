# Frontend Application (`frontend/`)

The client web interface for **ResearchAI**, built with React 18, TypeScript, Vite, and Tailwind CSS.

---

## Key Features

1. **Split-Screen Workspace:** Left panel hosts the structured 5-section academic summary and conversational Hybrid RAG chatbot; right panel hosts the embedded PDF viewer.
2. **Interactive PDF Viewing:** Displays research papers with page navigation, zoom, and highlight overlays corresponding to cited passages.
3. **Type Safety:** TypeScript contracts strictly mirror backend Pydantic models (`src/types/index.ts`).

---

## Local Development

```bash
cd frontend
npm install
npm run dev
```

The development server runs on `http://localhost:5173`.

## Real PDF uploads (Prompt 5)

The upload view posts one file to `POST /api/v1/documents`, shows the real server
response and status, and distinguishes a stored duplicate from a new upload.
A backend/network error stays an error and can be retried; no simulated document
is created. Pending documents keep their confirmation and original-PDF link
visible. The workspace action is offered only for `READY` documents.

Browser validation checks extension, MIME and a 25 MiB limit. The server also
checks actual bytes, PDF structure and its configurable size limit. Keep the
client cap aligned if changing the backend default.

```bash
npm test -- src/test/upload.test.tsx src/test/upload-integration.test.tsx src/test/upload-api.test.ts
```

Set `VITE_API_BASE_URL=http://localhost:8000/api/v1`. The client sets the multipart
boundary automatically; do not manually set a Content-Type on file uploads.
