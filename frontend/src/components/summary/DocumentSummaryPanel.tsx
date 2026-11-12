import { useEffect, useRef, useState } from 'react';
import { api, ApiError } from '../../services/api';
import { summaryCitation } from '../../services/citations';
import type { DocumentStatus } from '../../types';
import type { ChatCitation } from '../../types/chat';
import type { SummaryField, SummaryResponse, SummarySource } from '../../types/summary';

interface Props {
  documentId?: string;
  filename: string;
  documentStatus?: DocumentStatus;
  onCitationClick?: (citation: ChatCitation) => void;
}

const SECTIONS: { title: string; fields: SummaryField[] }[] = [
  { title: 'Title, Authors and Abstract', fields: ['title', 'authors', 'abstract'] },
  { title: 'Problem Statement', fields: ['problem_statement'] },
  { title: 'Methodology', fields: ['methodology'] },
  { title: 'Key Results', fields: ['key_results'] },
  { title: 'Conclusion', fields: ['conclusion'] },
];

export function DocumentSummaryPanel({ documentId, filename, documentStatus, onCitationClick }: Props) {
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [waiting, setWaiting] = useState(false);
  const [error, setError] = useState('');
  const [check, setCheck] = useState(0);
  const [sourceError, setSourceError] = useState('');
  const selection = useRef(0);
  const validId = !!documentId && /^[0-9a-f]{24}$/i.test(documentId);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    selection.current++;
    setSourceError('');
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
          if (documentStatus === 'FAILED') {
            setWaiting(false);
            setError('Analysis did not finish. Your original PDF is still available. Check the paper’s processing status to continue.');
          } else {
            setWaiting(true);
            timer = setTimeout(load, 5000);
          }
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
      selection.current++;
      if (timer) clearTimeout(timer);
    };
  }, [documentId, validId, documentStatus, check]);

  // Never show a previous document's result while a new request is in flight.
  const current = summary?.document_id === documentId?.toLowerCase() ? summary : null;
  async function openSource(source: SummarySource) {
    if (!current || !onCitationClick) return;
    const request = ++selection.current;
    setSourceError('');
    try {
      const citation = await summaryCitation(current, source);
      if (request === selection.current) onCitationClick(citation);
    } catch {
      if (request === selection.current) setSourceError('We couldn’t open this source. You can still view the original PDF.');
    }
  }
  return (
    <div className="min-w-0 w-full space-y-4 [overflow-wrap:anywhere]" aria-busy={loading}>
      <header className="ui-card p-5 sm:p-7">
        <p className="text-xs font-semibold text-blue-700">Research summary</p>
        <h2 className="mt-3 max-w-[70ch] text-xl font-semibold leading-8 tracking-tight text-slate-900 sm:text-2xl">{current?.title ?? filename}</h2>
      </header>
      {!validId && <p role="status" className="text-sm text-slate-600">This paper’s summary is not available. Choose an uploaded paper from your library.</p>}
      {loading && <p role="status" className="text-sm text-slate-600">Loading summary…</p>}
      {waiting && !loading && <p role="status" className="text-sm text-slate-600">Your paper is being analyzed. The summary will appear here when it is ready.</p>}
      {error && (
        <div role="alert" className="p-4 rounded-xl bg-red-50 text-sm text-red-800">
          <p>{error}</p>
          <button type="button" onClick={() => setCheck(value => value + 1)} className="ui-button ui-button-secondary mt-3">Check again</button>
        </div>
      )}
      {sourceError && <p role="alert" className="text-sm text-red-700">{sourceError}</p>}
      {(current || loading || waiting) && SECTIONS.map((section, index) => {
        const references = current?.sources.filter(source => section.fields.includes(source.field)) ?? [];
        const sources = references.filter((source, position) => references.findIndex(other =>
          other.chunk_id === source.chunk_id && other.page_number === source.page_number && other.quote === source.quote) === position);
        return (
          <section key={section.title} className="ui-card p-5 sm:p-7">
            <h3 className="flex items-center gap-3 text-base font-semibold text-slate-900"><span aria-hidden="true" className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-blue-100 bg-blue-50 text-xs font-semibold text-blue-700">{String(index + 1).padStart(2, '0')}</span>{section.title}</h3>
            <div className="mt-4 max-w-[100ch] text-sm leading-7 text-slate-700 whitespace-pre-wrap">
              {current ? section.fields.map(field => (
                <p key={field} className="mt-2">{field === 'authors'
                  ? `Authors: ${current.authors.length ? current.authors.join(', ') : 'Not stated in the document.'}`
                  : current[field]}</p>
              )) : <div aria-hidden="true" className="space-y-2 py-2"><div className="ui-skeleton h-3 w-full" /><div className="ui-skeleton h-3 w-4/5" /><div className="ui-skeleton h-3 w-3/5" /></div>}
            </div>
            {sources.length > 0 && <div className="mt-3">
              <div aria-label={'Sources for ' + section.title} className="flex flex-wrap gap-2 text-xs">
                {sources.map((source, sourceIndex) => onCitationClick
                  ? <button key={sourceIndex} type="button" onClick={event => { event.currentTarget.focus(); void openSource(source); }}
                    aria-label={'Open source for ' + section.title + ', page ' + source.page_number}
                    className="inline-flex min-h-8 items-center rounded-lg bg-blue-50 px-2.5 py-1 font-medium text-blue-700 hover:bg-blue-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600">Page {source.page_number}</button>
                  : <span key={sourceIndex} className="font-medium text-slate-500">Page {source.page_number}</span>)}
              </div>
              <details className="mt-3 text-xs text-slate-500">
                <summary className="min-h-8 w-fit cursor-pointer rounded py-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600">Supporting passages</summary>
                <ul className="mt-2 space-y-2">
                  {sources.map((source, sourceIndex) => <li key={sourceIndex}>
                    <blockquote className="border-l-2 border-slate-200 pl-2 leading-6">{source.quote}</blockquote>
                  </li>)}
                </ul>
              </details>
            </div>}
          </section>
        );
      })}
    </div>
  );
}
