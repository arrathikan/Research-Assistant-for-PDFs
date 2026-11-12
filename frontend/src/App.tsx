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
    <div className="h-dvh w-full min-w-0 flex flex-col overflow-hidden bg-slate-50">
      <Navbar activeFilename={activeDoc?.filename} status={activeDoc?.status} />
      <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        {activeDoc ? <DocumentWorkspace document={activeDoc} initialTab={workspaceTab} />
          : <UploadView onUploadSuccess={handleUploadSuccess} />}
      </main>
    </div>
  );
};

export default App;
