import { useEffect, useState } from 'react';
import { BookOpen, FileText, MessageSquare } from 'lucide-react';
import { PageContainer } from '../layout/PageContainer';
import type { DocumentMetadata, WorkspaceTab } from '../../types';
import type { ChatCitation } from '../../types/chat';
import { DocumentSummaryPanel } from '../summary/DocumentSummaryPanel';
import { DocumentChatPanel } from '../chat/DocumentChatPanel';
import { PdfViewerPanel } from '../pdf/PdfViewerPanel';

export function DocumentWorkspace({ document, initialTab = 'summary' }: { document: DocumentMetadata; initialTab?: WorkspaceTab }) {
  const [tab, setTab] = useState<WorkspaceTab>(initialTab);
  const [citation, setCitation] = useState<ChatCitation | null>(null);
  useEffect(() => { setCitation(null); setTab(initialTab); }, [document.id, initialTab]);
  function openSource(source: ChatCitation) {
    // A fresh selection lets the same source reopen after manual page navigation.
    setCitation({ ...source });
    if (window.innerWidth < 1024) setTab('pdf');
  }
  return (
    <PageContainer scrollable={false}>
      <nav aria-label="Workspace panels" className="flex shrink-0 flex-wrap gap-2 border-b border-slate-200 bg-white px-4 py-2 text-xs font-semibold">
        <button type="button" aria-pressed={tab === 'summary'} onClick={() => setTab('summary')} className="flex items-center gap-2 rounded p-2 aria-pressed:bg-blue-50 aria-pressed:text-blue-700"><BookOpen size={15} />Structured Summary</button>
        <button type="button" aria-pressed={tab === 'chat'} onClick={() => setTab('chat')} className="flex items-center gap-2 rounded p-2 aria-pressed:bg-blue-50 aria-pressed:text-blue-700"><MessageSquare size={15} />AI Chatbot</button>
        <button type="button" aria-pressed={tab === 'pdf'} onClick={() => setTab('pdf')} className="flex items-center gap-2 rounded p-2 lg:hidden aria-pressed:bg-blue-50 aria-pressed:text-blue-700"><FileText size={15} />PDF Viewer</button>
      </nav>
      <div className="grid min-h-0 min-w-0 flex-1 grid-cols-1 overflow-hidden lg:grid-cols-2">
        <section aria-label="Summary and chat" className={`${tab === 'pdf' ? 'hidden lg:block' : 'block'} min-h-0 min-w-0 overflow-y-auto border-slate-200 bg-slate-50 p-4 lg:border-r lg:p-6`}>
          <div hidden={tab !== 'summary'}><DocumentSummaryPanel documentId={document.id} filename={document.filename} /></div>
          <div hidden={tab === 'summary'}><DocumentChatPanel documentId={document.id} onCitationClick={openSource} /></div>
        </section>
        <section aria-label="PDF pane" className={`${tab === 'pdf' ? 'flex' : 'hidden'} min-h-0 min-w-0 flex-col lg:flex`}>
          <PdfViewerPanel document={document} activeCitation={citation} onClearCitation={() => setCitation(null)} />
        </section>
      </div>
    </PageContainer>
  );
}
