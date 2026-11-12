import React, { useState } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardView } from './views/DashboardView';
import { UploadView } from './views/UploadView';
import { DocumentWorkspace } from './components/workspace/DocumentWorkspace';
import { NavigationTab, DocumentMetadata, WorkspaceTab } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavigationTab>('dashboard');
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [activeDoc, setActiveDoc] = useState<DocumentMetadata | null>(null);

  const [workspaceTab, setWorkspaceTab] = useState<WorkspaceTab>('summary');

  const handleUploadSuccess = (newDoc: DocumentMetadata, tab: WorkspaceTab = 'summary') => {
    setWorkspaceTab(tab);
    // Add to library and immediately select as active workspace paper
    setDocuments((prev) => [newDoc, ...prev.filter(doc => doc.sha256 !== newDoc.sha256)]);
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
        />
      )}

      {activeTab === 'upload' && (
        <UploadView onUploadSuccess={handleUploadSuccess} />
      )}

      {activeTab === 'workspace' && activeDoc && (
        <DocumentWorkspace document={activeDoc} initialTab={workspaceTab} />
      )}
    </AppLayout>
  );
};

export default App;
