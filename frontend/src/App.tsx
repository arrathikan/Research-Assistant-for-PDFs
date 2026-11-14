import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardView } from './views/DashboardView';
import { UploadView } from './views/UploadView';
import { DocumentWorkspace } from './components/workspace/DocumentWorkspace';
import { api, ApiError } from './services/api';
import { readLibrarySession, saveLibrarySession } from './services/librarySession';
import { PageContainer } from './components/layout/PageContainer';
import { NavigationTab, DocumentMetadata, WorkspaceTab } from './types';

export const App: React.FC = () => {
  const [savedSession] = useState(readLibrarySession);
  const [restoration, setRestoration] = useState<'loading' | 'ready' | 'error'>(savedSession.ids.length ? 'loading' : 'ready');
  const [restoreAttempt, setRestoreAttempt] = useState(0);
  const navigationTouched = useRef(false);
  const [activeTab, setActiveTab] = useState<NavigationTab>('dashboard');
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [activeDoc, setActiveDoc] = useState<DocumentMetadata | null>(null);

  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const deletedIds = useRef(new Set<string>());
  const [workspaceTab, setWorkspaceTab] = useState<WorkspaceTab>('summary');

  const upsertDocument = useCallback((document: DocumentMetadata) => {
    if (document.id && deletedIds.current.has(document.id)) return;
    setDocuments(previous => {
      const existing = previous.find(item => item.sha256 === document.sha256);
      if (existing && JSON.stringify(existing) === JSON.stringify(document)) return previous;
      return existing ? previous.map(item => item.sha256 === document.sha256 ? document : item) : [document, ...previous];
    });
    setActiveDoc(previous => previous?.id === document.id ? document : previous);
  }, []);
  useEffect(() => {
    if (!savedSession.ids.length) return;
    let stopped = false;
    setRestoration('loading');
    Promise.all(savedSession.ids.map(async id => {
      try {
        const document = await api.getDocument(id);
        if (document.id !== id) throw new Error('Document mismatch');
        return document;
      } catch (failure) {
        if (failure instanceof ApiError && failure.status === 404) return null;
        throw failure;
      }
    })).then(restored => {
      if (stopped) return;
      const papers = restored.filter((paper): paper is DocumentMetadata => paper !== null);
      setDocuments(papers);
      const selected = papers.find(paper => paper.id === savedSession.activeId) ?? null;
      setActiveDoc(selected);
      setWorkspaceTab(savedSession.workspaceTab);
      if (!navigationTouched.current) setActiveTab(savedSession.activeTab === 'workspace' && !selected ? 'dashboard' : savedSession.activeTab);
      setRestoration('ready');
    }).catch(() => { if (!stopped) setRestoration('error'); });
    return () => { stopped = true; };
  }, [savedSession, restoreAttempt]);

  useEffect(() => {
    if (restoration !== 'ready') return;
    saveLibrarySession({ ids: documents.flatMap(paper => paper.id ? [paper.id] : []), activeId: activeDoc?.id, activeTab, workspaceTab });
  }, [documents, activeDoc, activeTab, workspaceTab, restoration]);

  const pendingIds = documents.filter(item => item.status !== 'READY').map(item => item.id).filter(Boolean).join(',');
  useEffect(() => {
    if (!pendingIds || uploadModalOpen) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    async function refresh() {
      await Promise.all(pendingIds.split(',').map(async id => {
        try { const document = await api.getDocument(id); if (!stopped && document.id === id) upsertDocument(document); }
        catch { /* Keep the last confirmed metadata; a failed lookup never invents a status or removal. */ }
      }));
      if (!stopped) timer = setTimeout(refresh, 3000);
    }
    void refresh();
    return () => { stopped = true; if (timer) clearTimeout(timer); };
  }, [pendingIds, uploadModalOpen, upsertDocument]);

  async function deletePaper(document: DocumentMetadata) {
    if (!document.id) return;
    await api.deleteDocument(document.id);
    deletedIds.current.add(document.id);
    setDocuments(previous => previous.filter(item => item.id !== document.id));
    setActiveDoc(previous => previous?.id === document.id ? null : previous);
    try { sessionStorage.removeItem('researchai.chat.' + document.id); } catch { /* Optional storage. */ }
    if (activeDoc?.id === document.id) setActiveTab('dashboard');
  }

  const handleUploadSuccess = (newDoc: DocumentMetadata, tab: WorkspaceTab = 'summary') => {
    setWorkspaceTab(tab);
    upsertDocument(newDoc);
    setActiveDoc(newDoc);
    setActiveTab('workspace');
  };

  const handleSelectDocument = (doc: DocumentMetadata, tab: WorkspaceTab = 'summary') => {
    setWorkspaceTab(tab);
    setActiveDoc(doc);
    setActiveTab('workspace');
  };

  return (
    <AppLayout
      activeTab={activeTab}
      onSelectTab={tab => { navigationTouched.current = true; setActiveTab(tab); }}
      activeDoc={activeDoc}
    >
      {restoration !== 'ready' && <PageContainer>
        {restoration === 'loading' ? <p role="status" className="text-sm text-stone-600">Restoring your papers…</p>
          : <div role="alert" className="ui-card p-5"><p className="text-sm text-stone-700">We couldn’t restore your library. Your saved papers have not been removed.</p><button type="button" onClick={() => setRestoreAttempt(value => value + 1)} className="ui-button ui-button-secondary mt-4">Retry loading papers</button></div>}
      </PageContainer>}
      {restoration === 'ready' && activeTab === 'dashboard' && (
        <DashboardView
          documents={documents}
          onSelectDocument={handleSelectDocument}
          onNavigateUpload={() => setActiveTab('upload')}
          onDeleteDocument={deletePaper}
        />
      )}

      <UploadView active={restoration === 'ready' && activeTab === 'upload'} onUploadSuccess={handleUploadSuccess} onStored={upsertDocument}
        onModalChange={setUploadModalOpen} onGoToDashboard={() => setActiveTab('dashboard')} />

      {restoration === 'ready' && activeTab === 'workspace' && activeDoc && (
        <DocumentWorkspace document={activeDoc} initialTab={workspaceTab} onTabChange={setWorkspaceTab} />
      )}
    </AppLayout>
  );
};

export default App;
