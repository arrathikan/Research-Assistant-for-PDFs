import { useEffect, useState } from 'react';
import { api, ApiError } from '../../services/api';
import type { SummaryField, SummaryResponse } from '../../types/summary';

interface Props {
  documentId?: string;
  filename: string;
}

const SECTIONS: { title: string; fields: SummaryField[] }[] = [
  { title: 'Title, Authors and Abstract', fields: ['title', 'authors', 'abstract'] },
  { title: 'Problem Statement', fields: ['problem_statement'] },
  { title: 'Methodology', fields: ['methodology'] },
  { title: 'Key Results', fields: ['key_results'] },
  { title: 'Conclusion', fields: ['conclusion'] },
];

export function DocumentSummaryPanel({ documentId, filename }: Props) {
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [waiting, setWaiting] = useState(false);
  const [error, setError] = useState('');
  const [check, setCheck] = useState(0);
  const validId = !!documentId && /^[0-9a-f]{24}$/i.test(documentId);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    setSummary(null);
    setError('');
    setWaiting(false);
    setLoading(validId);
    if (!documentId || !validId) return;
    const id = documentId;

    async function load() {
      try {
        const result = await api.getDocumentSummary(id);
        if (cancelled) return;
        if (result.document_id !== id.toLowerCase()) {
          setError('The summary could not be matched to this document.');
          return;
        }
        setSummary(result);
        setWaiting(false);
        setError('');
      } catch (failure: unknown) {
        if (cancelled) return;
        if (failure instanceof ApiError && failure.status === 409) {
          setWaiting(true);
          timer = setTimeout(load, 5000);
        } else {
          setWaiting(false);
          setError(failure instanceof ApiError && failure.status === 404
            ? 'This document could not be found.'
            : 'The summary is unavailable. Please check again shortly.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [documentId, validId, check]);

  // Never show a previous document's result while a new request is in flight.
  const current = summary?.document_id === documentId?.toLowerCase() ? summary : null;
  return (
    <div className="min-w-0 w-full space-y-4 [overflow-wrap:anywhere]" aria-busy={loading}>
      <header className="p-5 bg-white rounded-2xl border border-slate-200">
        <p className="text-xs font-semibold text-blue-700">Research summary</p>
        <h2 className="text-base font-bold text-slate-900 mt-2">{current?.title ?? filename}</h2>
      </header>
      {!validId && <p role="status" className="text-sm text-slate-600">Upload a PDF to view its generated summary.</p>}
      {loading && <p role="status" className="text-sm text-slate-600">Loading summary…</p>}
      {waiting && !loading && <p role="status" className="text-sm text-slate-600">Summary not ready yet. Checking for updates…</p>}
      {error && (
        <div role="alert" className="p-4 rounded-xl bg-red-50 text-sm text-red-800">
          <p>{error}</p>
          <button type="button" onClick={() => setCheck(value => value + 1)} className="mt-2 font-semibold underline">Check again</button>
        </div>
      )}
      {SECTIONS.map((section, index) => {
        const references = current?.sources.filter(source => section.fields.includes(source.field)) ?? [];
        const sources = references.filter((source, position) => references.findIndex(other =>
          other.chunk_id === source.chunk_id && other.page_number === source.page_number && other.quote === source.quote) === position);
        return (
          <section key={section.title} className="p-5 bg-white rounded-2xl border border-slate-200">
            <h3 className="text-sm font-bold text-slate-800"><span aria-hidden="true">{index + 1}. </span>{section.title}</h3>
            <div className="mt-3 text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">
              {current ? section.fields.map(field => (
                <p key={field} className="mt-2">{field === 'authors'
                  ? `Authors: ${current.authors.length ? current.authors.join(', ') : 'Not stated in the document.'}`
                  : current[field]}</p>
              )) : <p>Waiting for a generated summary.</p>}
            </div>
            {sources.length > 0 && (
              <ul aria-label={`Sources for ${section.title}`} className="mt-3 space-y-2 text-xs text-slate-500">
                {sources.map((source, sourceIndex) => (
                  <li key={`${source.chunk_id}-${source.page_number}-${sourceIndex}`}>
                    <span className="font-semibold">Page {source.page_number}</span>
                    <blockquote className="mt-1 border-l-2 border-slate-200 pl-2">{source.quote}</blockquote>
                  </li>
                ))}
              </ul>
            )}
          </section>
        );
      })}
    </div>
  );
}
