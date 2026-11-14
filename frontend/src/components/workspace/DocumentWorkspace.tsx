import { lazy, Suspense, useEffect, useId, useRef, useState } from 'react';
import { BookOpen, FileText, MessageSquare, X } from 'lucide-react';
import { PageContainer } from '../layout/PageContainer';
import type { DocumentMetadata, WorkspaceTab } from '../../types';
import type { ChatCitation } from '../../types/chat';
import { DocumentSummaryPanel } from '../summary/DocumentSummaryPanel';
import { DocumentChatPanel } from '../chat/DocumentChatPanel';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { PdfViewerBoundary } from '../pdf/PdfViewerBoundary';
import { DocumentStatusBadge } from '../common/DocumentStatusBadge';

const PdfViewerPanel = lazy(() => import('../pdf/PdfViewerPanel').then(module => ({ default: module.PdfViewerPanel })));

interface Props { document: DocumentMetadata; initialTab?: WorkspaceTab; onTabChange?: (tab: 'summary' | 'chat') => void; }

export function DocumentWorkspace(props: Props) {
  // Document switches reset navigation synchronously; toggling the PDF never remounts this session.
  return <WorkspaceSession key={props.document.id ?? props.document.sha256} {...props} />;
}

function WorkspaceSession({ document: paper, initialTab = 'summary', onTabChange }: Props) {
  const panelId = useId();
  const [tab, setTab] = useState<'summary' | 'chat'>(initialTab === 'chat' ? 'chat' : 'summary');
  useEffect(() => { onTabChange?.(tab); }, [tab, onTabChange]);
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

  function switchTab(event: React.KeyboardEvent<HTMLButtonElement>, next: 'summary' | 'chat') {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const target = event.key === 'Home' ? 'summary' : event.key === 'End' ? 'chat' : next;
    setTab(target);
    window.document.getElementById(panelId + '-' + target)?.focus();
  }

  useEffect(() => {
    if (!pdfOpen || !mobile) return;
    const navigation = Array.from(window.document.querySelectorAll('[data-app-header], [data-app-navigation]'));
    const previous = navigation.map(element => element.hasAttribute('inert'));
    navigation.forEach(element => element.setAttribute('inert', ''));
    return () => { navigation.forEach((element, index) => { if (!previous[index]) element.removeAttribute('inert'); }); };
  }, [pdfOpen, mobile]);

  const contentWidth = pdfOpen ? '' : 'max-w-[1200px]';
  return (
    <PageContainer scrollable={false}>
      <div hidden={pdfOpen && mobile} className="shrink-0 border-b border-stone-200 bg-white py-3">
        <div className={'mx-auto w-full min-w-0 ' + contentWidth}>
          <div className="mb-4 flex min-w-0 flex-wrap items-center gap-3">
            <div className="min-w-0 flex-1"><p className="ui-eyebrow mb-1">Research workspace</p><h1 className="break-words text-base font-semibold text-stone-900 [overflow-wrap:anywhere] sm:text-lg">{paper.filename}</h1></div>
            <DocumentStatusBadge status={paper.status} />
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3">
          <nav role="tablist" aria-label="Workspace panels" className="flex min-w-0 flex-wrap gap-1">
            <button type="button" role="tab" id={panelId + '-summary'} aria-selected={tab === 'summary'} tabIndex={tab === 'summary' ? 0 : -1} onKeyDown={event => switchTab(event, 'chat')} onClick={() => setTab('summary')}
              className="ui-tab">
              <BookOpen size={15} aria-hidden="true" />Structured Summary
            </button>
            <button type="button" role="tab" id={panelId + '-chat'} aria-selected={tab === 'chat'} tabIndex={tab === 'chat' ? 0 : -1} onKeyDown={event => switchTab(event, 'summary')} onClick={() => setTab('chat')}
              className="ui-tab">
              <MessageSquare size={15} aria-hidden="true" />AI Chatbot
            </button>
          </nav>
          <button type="button" disabled={!validDocument} aria-expanded={pdfOpen} aria-controls="workspace-original-pdf"
            onClick={event => { event.currentTarget.focus(); if (pdfOpen) setPdfOpen(false); else showPdf(); }}
            className="ui-button ui-button-secondary ui-link text-xs">
            <FileText size={15} aria-hidden="true" />{pdfOpen ? 'Close PDF' : 'View Original PDF'}
          </button>
          </div>
        </div>
      </div>
      <div data-testid="workspace-grid" className={'grid min-h-0 min-w-0 flex-1 overflow-hidden '
        + (pdfOpen ? 'grid-cols-1 md:grid-cols-[minmax(0,11fr)_minmax(0,9fr)]' : 'grid-cols-1')}>
        <section aria-label="Summary and chat" hidden={pdfOpen && mobile}
          className={'min-h-0 min-w-0 overflow-y-auto bg-stone-50 py-5 '
            + (pdfOpen ? 'md:border-r md:border-stone-200 md:pr-5' : '')}>
          <div className={'mx-auto w-full min-w-0 ' + contentWidth}>
            {sourceError && <p role="alert" className="mb-4 rounded-lg border border-red-200 bg-white p-3 text-sm text-red-700">{sourceError}</p>}
            <div role="tabpanel" aria-labelledby={panelId + '-summary'} hidden={tab !== 'summary'}>
              <DocumentSummaryPanel documentId={paper.id} filename={paper.filename} documentStatus={paper.status} onCitationClick={openSource} />
            </div>
            <div role="tabpanel" aria-labelledby={panelId + '-chat'} hidden={tab !== 'chat'}>
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
          {mobile && <div className="flex shrink-0 items-center justify-between gap-2 border-b border-stone-200 bg-white px-3 py-2">
            <p className="min-w-0 truncate text-xs font-semibold text-stone-700">Original PDF</p>
            <button ref={closeButton} type="button" onClick={() => setPdfOpen(false)}
              className="ui-button ui-button-ghost">
              <X size={15} aria-hidden="true" />Close PDF
            </button>
          </div>}
          <div className="min-h-0 min-w-0 flex-1">
            <PdfViewerBoundary documentId={paper.id}>
              <Suspense fallback={<LoadingSpinner label="Opening PDF viewer…" />}>
                <PdfViewerPanel document={paper} activeCitation={citation} onClearCitation={() => setCitation(null)} />
              </Suspense>
            </PdfViewerBoundary>
          </div>
        </aside>}
      </div>
    </PageContainer>
  );
}
