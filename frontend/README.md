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
