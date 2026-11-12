import { useEffect, useRef, useState } from 'react';
import { BookOpen, FileText, MessageSquare, X } from 'lucide-react';
import { PageContainer } from '../layout/PageContainer';
import type { DocumentMetadata, WorkspaceTab } from '../../types';
import type { ChatCitation } from '../../types/chat';
import { DocumentSummaryPanel } from '../summary/DocumentSummaryPanel';
import { DocumentChatPanel } from '../chat/DocumentChatPanel';
import { PdfViewerPanel } from '../pdf/PdfViewerPanel';

interface Props { document: DocumentMetadata; initialTab?: WorkspaceTab; }

export function DocumentWorkspace(props: Props) {
  // Document switches reset navigation synchronously; toggling the PDF never remounts this session.
  return <WorkspaceSession key={props.document.id ?? props.document.sha256} {...props} />;
}

function WorkspaceSession({ document: paper, initialTab = 'summary' }: Props) {
  const [tab, setTab] = useState(initialTab === 'chat' ? 'chat' : 'summary');
  const [pdfOpen, setPdfOpen] = useState(false);
  const [pdfLoaded, setPdfLoaded] = useState(false);
  const [citation, setCitation] = useState<ChatCitation | null>(null);
  const [sourceError, setSourceError] = useState('');
  const [mobile, setMobile] = useState(window.innerWidth < 768);
  const pdfPane = useRef<HTMLElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const opener = useRef<HTMLElement | null>(null);
  const validDocument = !!paper.id && /^[0-9a-f]{24}$/i.test(paper.id);

  function showPdf() {
    if (!validDocument) return;
    if (!pdfOpen) opener.current = window.document.activeElement as HTMLElement | null;
    setPdfLoaded(true);
    setPdfOpen(true);
  }

  useEffect(() => {
    if (initialTab === 'pdf') {
      if (validDocument) { setPdfLoaded(true); setPdfOpen(true); }
    } else setTab(initialTab);
  }, [initialTab, validDocument]);

  useEffect(() => {
    const resize = () => setMobile(window.innerWidth < 768);
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);

  useEffect(() => {
    if (!pdfOpen) return;
    const previous = opener.current;
    if (mobile) closeButton.current?.focus();
    const keyboard = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.preventDefault(); setPdfOpen(false); }
      if (!mobile || event.key !== 'Tab') return;
      const controls = pdfPane.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), a[href], input:not([disabled]), [tabindex="0"]',
      );
      if (!controls?.length) return;
      const first = controls[0], last = controls[controls.length - 1];
      if (!pdfPane.current?.contains(window.document.activeElement)) {
        event.preventDefault(); first.focus(); return;
      }
      if (event.shiftKey && window.document.activeElement === first) {
        event.preventDefault(); last.focus();
      } else if (!event.shiftKey && window.document.activeElement === last) {
        event.preventDefault(); first.focus();
      }
    };
    window.document.addEventListener('keydown', keyboard);
    return () => {
      window.document.removeEventListener('keydown', keyboard);
      if (mobile && previous?.isConnected) previous.focus();
    };
  }, [pdfOpen, mobile]);

  function openSource(source: ChatCitation) {
    if (!validDocument || source.document_id !== paper.id?.toLowerCase()) {
      setSourceError('This source is not available for the selected paper. Try another citation.');
      return;
    }
    if (!Number.isInteger(source.page_number) || source.page_number < 1
      || (paper.page_count && source.page_number > paper.page_count)) {
      setSourceError('That source page is not available in this paper. Try another citation.');
      return;
    }
    setSourceError('');
    setCitation({ ...source });
    showPdf();
  }

  const contentWidth = pdfOpen ? '' : 'max-w-[1200px]';
  return (
    <PageContainer scrollable={false}>
      <div hidden={pdfOpen && mobile} className="shrink-0 border-b border-slate-200 bg-white py-3">
        <div className={'mx-auto flex w-full min-w-0 flex-wrap items-center justify-between gap-3 ' + contentWidth}>
          <nav aria-label="Workspace panels" className="flex flex-wrap gap-1 text-xs font-semibold">
            <button type="button" aria-pressed={tab === 'summary'} onClick={() => setTab('summary')}
              className="flex min-h-10 items-center gap-2 rounded-lg px-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 aria-pressed:bg-blue-50 aria-pressed:text-blue-700">
              <BookOpen size={15} aria-hidden="true" />Structured Summary
            </button>
            <button type="button" aria-pressed={tab === 'chat'} onClick={() => setTab('chat')}
              className="flex min-h-10 items-center gap-2 rounded-lg px-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 aria-pressed:bg-blue-50 aria-pressed:text-blue-700">
              <MessageSquare size={15} aria-hidden="true" />AI Chatbot
            </button>
          </nav>
          <button type="button" disabled={!validDocument} aria-expanded={pdfOpen} aria-controls="workspace-original-pdf"
            onClick={event => { event.currentTarget.focus(); if (pdfOpen) setPdfOpen(false); else showPdf(); }}
            className="flex min-h-10 items-center justify-center gap-2 rounded-lg border border-blue-200 bg-white px-3 text-xs font-semibold text-blue-700 hover:bg-blue-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 disabled:opacity-50">
            <FileText size={15} aria-hidden="true" />{pdfOpen ? 'Close PDF' : 'View Original PDF'}
          </button>
        </div>
      </div>
      <div data-testid="workspace-grid" className={'grid min-h-0 min-w-0 flex-1 overflow-hidden '
        + (pdfOpen ? 'grid-cols-1 md:grid-cols-[minmax(0,11fr)_minmax(0,9fr)]' : 'grid-cols-1')}>
        <section aria-label="Summary and chat" hidden={pdfOpen && mobile}
          className={'min-h-0 min-w-0 overflow-y-auto bg-slate-50 py-5 '
            + (pdfOpen ? 'md:border-r md:border-slate-200 md:pr-5' : '')}>
          <div className={'mx-auto w-full min-w-0 ' + contentWidth}>
            {sourceError && <p role="alert" className="mb-4 rounded-lg border border-red-200 bg-white p-3 text-sm text-red-700">{sourceError}</p>}
            <div hidden={tab !== 'summary'}>
              <DocumentSummaryPanel documentId={paper.id} filename={paper.filename} onCitationClick={openSource} />
            </div>
            <div hidden={tab !== 'chat'}>
              <DocumentChatPanel documentId={paper.id} onCitationClick={openSource} />
            </div>
          </div>
        </section>
        {pdfLoaded && <aside id="workspace-original-pdf" ref={pdfPane} hidden={!pdfOpen}
          role={mobile && pdfOpen ? 'dialog' : 'region'} aria-modal={mobile && pdfOpen ? true : undefined}
          aria-label="Original PDF"
          className={pdfOpen
            ? 'fixed inset-0 z-50 flex min-h-0 min-w-0 flex-col bg-white md:static md:z-auto'
            : 'hidden'}>
          {mobile && <div className="flex shrink-0 items-center justify-between gap-2 border-b border-slate-200 bg-white px-3 py-2">
            <p className="min-w-0 truncate text-xs font-semibold text-slate-700">Original PDF</p>
            <button ref={closeButton} type="button" onClick={() => setPdfOpen(false)}
              className="flex min-h-10 items-center gap-1 rounded-lg px-3 text-xs font-semibold text-slate-600 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600">
              <X size={15} aria-hidden="true" />Close PDF
            </button>
          </div>}
          <div className="min-h-0 min-w-0 flex-1">
            <PdfViewerPanel document={paper} activeCitation={citation} onClearCitation={() => setCitation(null)} />
          </div>
        </aside>}
      </div>
    </PageContainer>
  );
}
