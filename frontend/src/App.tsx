import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardView } from './views/DashboardView';
import { UploadView } from './views/UploadView';
import { DocumentWorkspace } from './components/workspace/DocumentWorkspace';
import { api } from './services/api';
import { NavigationTab, DocumentMetadata, WorkspaceTab } from './types';

export const App: React.FC = () => {
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
      onSelectTab={setActiveTab}
      activeDoc={activeDoc}
    >
      {activeTab === 'dashboard' && (
        <DashboardView
          documents={documents}
          onSelectDocument={handleSelectDocument}
          onNavigateUpload={() => setActiveTab('upload')}
          onDeleteDocument={deletePaper}
        />
      )}

      <UploadView active={activeTab === 'upload'} onUploadSuccess={handleUploadSuccess} onStored={upsertDocument}
        onModalChange={setUploadModalOpen} onGoToDashboard={() => setActiveTab('dashboard')} />

      {activeTab === 'workspace' && activeDoc && (
        <DocumentWorkspace document={activeDoc} initialTab={workspaceTab} />
      )}
    </AppLayout>
  );
};

export default App;
