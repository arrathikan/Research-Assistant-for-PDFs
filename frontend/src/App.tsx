import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { DocumentMetadata, WorkspaceTab } from './types';
import { UploadView } from './views/UploadView';
import { DocumentWorkspace } from './components/workspace/DocumentWorkspace';

export const App: React.FC = () => {
  const [activeDoc, setActiveDoc] = useState<DocumentMetadata | null>(null);
  const [workspaceTab, setWorkspaceTab] = useState<WorkspaceTab>('summary');
  const handleUploadSuccess = (document: DocumentMetadata, tab: WorkspaceTab = 'summary') => {
    setActiveDoc(document);
    setWorkspaceTab(tab);
  };
  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-slate-50">
      <Navbar activeFilename={activeDoc?.filename} status={activeDoc?.status} />
      {activeDoc ? <DocumentWorkspace document={activeDoc} initialTab={workspaceTab} /> : (
        <div className="flex-1 overflow-auto"><UploadView onUploadSuccess={handleUploadSuccess} /></div>
      )}
    </div>
  );
};

export default App;
