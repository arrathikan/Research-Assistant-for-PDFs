import { useCallback, useEffect, useRef, useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist';
import 'react-pdf/dist/Page/TextLayer.css';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import { api, ApiError } from '../../services/api';
import type { DocumentMetadata } from '../../types';
import type { ChatCitation } from '../../types/chat';
import { findTextRange, rangeRects, regionRects } from './highlights';
import type { PageFrame, Rect } from './highlights';

pdfjs.GlobalWorkerOptions.workerSrc = new URL('pdfjs-dist/build/pdf.worker.min.js', import.meta.url).toString();
const assets = `${import.meta.env.BASE_URL}pdfjs/${pdfjs.version}/`;
const OPTIONS = { cMapUrl: `${assets}cmaps/`, cMapPacked: true, standardFontDataUrl: `${assets}standard_fonts/`, isEvalSupported: false };
interface Props { document: DocumentMetadata; activeCitation?: ChatCitation | null; onClearCitation?: () => void; }
type Highlight = { kind: 'text' | 'region' | 'page'; rects: Rect[] };

export function PdfViewerPanel({ document: paper, activeCitation, onClearCitation }: Props) {
  const id = paper.id;
  const valid = !!id && /^[0-9a-f]{24}$/i.test(id);
  const latestId = useRef(id);
  latestId.current = id;
  const viewport = useRef<HTMLDivElement>(null);
  const pageBox = useRef<HTMLDivElement>(null);
  const [loaded, setLoaded] = useState<{ id: string; pages: number } | null>(null);
  const [pageState, setPage] = useState({ id, value: 1 });
  const page = pageState.id === id ? pageState.value : 1;
  const pages = loaded && loaded.id === id ? loaded.pages : 0;
  const [zoom, setZoom] = useState(100);
  const [width, setWidth] = useState(600);
  const [retry, setRetry] = useState(0);
  const [pdfError, setPdfError] = useState('');
  const [sourceError, setSourceError] = useState('');
  const [resolving, setResolving] = useState(false);
  const [source, setSource] = useState<ChatCitation | null>(null);
  const [frameState, setFrame] = useState<{ id?: string; page: number; value: PageFrame } | null>(null);
  const frame = frameState && frameState.id === id && frameState.page === page ? frameState.value : null;
  const renderKey = `${id}-${page}-${width}-${zoom}`;
  const latestRenderKey = useRef(renderKey);
  latestRenderKey.current = renderKey;
  const latestPage = useRef(page);
  latestPage.current = page;
  const [renderedKey, setRenderedKey] = useState('');
  const [textRevision, setTextRevision] = useState(0);
  const [highlight, setHighlight] = useState<Highlight>({ kind: 'page', rects: [] });
  const anchor = source && source.document_id === id?.toLowerCase() && source.citation_id === activeCitation?.citation_id ? source : null;

  useEffect(() => {
    setLoaded(null); setPage({ id, value: 1 }); setZoom(100); setPdfError(''); setSource(null);
    setFrame(null); setHighlight({ kind: 'page', rects: [] });
  }, [id]);
  useEffect(() => {
    const element = viewport.current;
    if (!element) return;
    const measure = () => { if (element.clientWidth > 0) setWidth(Math.max(200, element.clientWidth - 32)); };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    let cancelled = false;
    setSource(null); setSourceError(''); setHighlight({ kind: 'page', rects: [] }); setResolving(false);
    if (!activeCitation || !id || !valid) return;
    const citation = activeCitation;
    if (citation.document_id !== id.toLowerCase()) { setSourceError('This citation belongs to a different document.'); return; }
    setResolving(true);
    void api.resolveCitation(id, citation).then(result => {
      if (cancelled) return;
      if (result.document_id !== id.toLowerCase() || result.citation_id !== citation.citation_id || result.chunk_id !== citation.chunk_id || result.page_number !== citation.page_number || result.quote_snippet !== citation.quote_snippet || !result.chunk_set_id || !result.parse_run_id) {
        throw new Error('Citation source mismatch');
      }
      setSource(result); setPage({ id, value: result.page_number });
    }).catch((failure: unknown) => {
      if (!cancelled) setSourceError(failure instanceof ApiError && failure.status === 409
        ? 'This source changed. Load a current answer before opening the citation.'
        : 'This citation could not be verified. No highlight was applied.');
    }).finally(() => { if (!cancelled) setResolving(false); });
    return () => { cancelled = true; };
  }, [id, valid, activeCitation]);

  const textRendered = useCallback(() => setTextRevision(value => value + 1), []);
  const pageLoaded = useCallback((pdfPage: PDFPageProxy) => {
    if (latestId.current !== id || latestPage.current !== pdfPage.pageNumber) return;
    const view = pdfPage.getViewport({ scale: 1 });
    setFrame({ id, page: pdfPage.pageNumber, value: { width: view.width, height: view.height, rotation: pdfPage.rotate, cropX: pdfPage.view[0], cropY: pdfPage.view[1], userUnit: pdfPage.userUnit } });
  }, [id]);
  const canvasRendered = useCallback(() => { if (latestRenderKey.current === renderKey) setRenderedKey(renderKey); }, [renderKey]);
  const documentLoaded = useCallback((pdf: PDFDocumentProxy) => {
    if (latestId.current === id && id) { setLoaded({ id, pages: pdf.numPages }); setPdfError(''); }
  }, [id]);

  useEffect(() => {
    setHighlight({ kind: 'page', rects: [] });
    if (!anchor || page !== anchor.page_number || !pages || page < 1 || page > pages || !frame || renderedKey !== renderKey) return;
    const tick = requestAnimationFrame(() => {
      const box = pageBox.current;
      if (!box) return;
      const bounds = box.getBoundingClientRect();
      if (bounds.width <= 0 || bounds.height <= 0) return;
      const textLayer = box.querySelector<HTMLElement>('.react-pdf__Page__textContent');
      let result: Highlight = { kind: 'page', rects: [] };
      if (textLayer) {
        const match = findTextRange(textLayer, anchor.quote_snippet);
        if (match.range) {
          const rects = rangeRects(match.range, bounds);
          if (rects.length) result = { kind: 'text', rects };
        }
      }
      if (result.kind === 'page') {
        const regions = regionRects(anchor, frame);
        if (regions.length) result = { kind: 'region', rects: regions.map(rect => ({ left: rect.left * bounds.width, top: rect.top * bounds.height, width: rect.width * bounds.width, height: rect.height * bounds.height })) };
      }
      setHighlight(result);
      const scroll = viewport.current;
      if (scroll) {
        const first = result.rects[0];
        const container = scroll.getBoundingClientRect();
        scroll.scrollTo({ top: first ? Math.max(0, bounds.top - container.top + scroll.scrollTop + first.top - 64) : 0,
          left: first ? Math.max(0, bounds.left - container.left + scroll.scrollLeft + first.left - 32) : 0, behavior: 'smooth' });
      }
    });
    return () => cancelAnimationFrame(tick);
  }, [anchor, page, pages, frame, width, zoom, textRevision, renderKey, renderedKey]);

  const targetInvalid = !!anchor && pages > 0 && anchor.page_number > pages;
  return (
    <section data-testid="pdf-viewer-panel" aria-label="PDF source viewer" className="flex min-h-0 h-full flex-col bg-slate-100">
      <div className="flex flex-wrap items-center gap-2 border-b bg-white p-3 text-xs">
        <button type="button" aria-label="Previous Page" disabled={!pages || page <= 1} onClick={() => setPage({ id, value: page - 1 })}>Previous</button>
        <label>Page <input aria-label="PDF page number" type="number" min={1} max={pages || 1} value={page} disabled={!pages} onChange={event => { const next = Number(event.target.value); if (Number.isInteger(next) && next >= 1 && next <= pages) setPage({ id, value: next }); }} className="w-14 rounded border p-1" /></label>
        <span>of {pages || '…'}</span>
        <button type="button" aria-label="Next Page" disabled={!pages || page >= pages} onClick={() => setPage({ id, value: page + 1 })}>Next</button>
        <button type="button" aria-label="Zoom Out" disabled={zoom <= 50} onClick={() => setZoom(value => Math.max(50, value - 25))}>−</button>
        <span aria-label="PDF zoom">{zoom}%</span>
        <button type="button" aria-label="Zoom In" disabled={zoom >= 200} onClick={() => setZoom(value => Math.min(200, value + 25))}>+</button>
        <button type="button" aria-label="Reset Zoom" onClick={() => setZoom(100)}>Reset zoom</button>
        {valid && id && <a className="ml-auto underline" href={api.getPdfStreamUrl(id)} target="_blank" rel="noreferrer">Open original PDF</a>}
      </div>
      {resolving && <p role="status" className="p-3 text-sm">Opening citation…</p>}
      {sourceError && <p role="alert" className="p-3 text-sm text-red-700">{sourceError}</p>}
      {targetInvalid && <p role="alert" className="p-3 text-sm text-red-700">The citation page is outside this PDF. No highlight was applied.</p>}
      {anchor && !targetInvalid && (
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-blue-100 bg-white px-3 py-2 text-xs text-slate-600">
          <p className="font-medium">Source — Page {anchor.page_number}</p>
          <div className="flex items-center gap-2">
            {page !== anchor.page_number && <button type="button" onClick={() => setPage({ id, value: anchor.page_number })} className="rounded px-2 py-1 font-medium text-blue-700 hover:bg-blue-50">Return to source</button>}
            {onClearCitation && <button type="button" className="rounded px-2 py-1 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600" onClick={onClearCitation}>Clear source</button>}
          </div>
        </div>
      )}
      <div ref={viewport} className="min-h-0 flex-1 overflow-auto p-4">
        {!valid ? <p role="status">Upload a PDF to view its pages.</p> : (
          <Document key={`${id}-${retry}`} file={api.getPdfStreamUrl(id!)} options={OPTIONS} onLoadSuccess={documentLoaded}
            onLoadError={() => setPdfError('The PDF could not be loaded.')} loading={<p role="status">Loading PDF…</p>}
            error={<p role="alert">The PDF could not be loaded.</p>}>
            {pages > 0 && page >= 1 && page <= pages && (
              <div ref={pageBox} className="relative inline-block bg-white shadow-sm">
                <Page key={`${page}-${width}-${zoom}`} pageNumber={page} width={width * zoom / 100} onLoadSuccess={pageLoaded}
                  onRenderSuccess={canvasRendered} onRenderTextLayerSuccess={textRendered} onRenderTextLayerError={textRendered} renderTextLayer renderAnnotationLayer
                  loading={<p role="status">Rendering page…</p>} error={<p role="alert">This PDF page could not be rendered.</p>} />
                <div aria-hidden="true" className="pointer-events-none absolute inset-0" data-highlight-kind={highlight.kind}>
                  {(anchor && page === anchor.page_number && renderedKey === renderKey ? highlight.rects : []).map((rect, index) => <div key={index} data-testid="pdf-source-highlight" style={{ position: 'absolute', ...rect, background: 'rgba(250, 204, 21, 0.4)', outline: highlight.kind === 'region' ? '2px solid #d97706' : undefined, mixBlendMode: 'multiply' }} />)}
                </div>
              </div>
            )}
          </Document>
        )}
        {pdfError && <button type="button" onClick={() => { setPdfError(''); setLoaded(null); setRetry(value => value + 1); }} className="mt-3 underline">Retry PDF</button>}
      </div>
    </section>
  );
}
