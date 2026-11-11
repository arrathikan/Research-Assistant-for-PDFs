import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { DocumentMetadata } from './types';
import { UploadView } from './views/UploadView';
import { DocumentWorkspace } from './components/workspace/DocumentWorkspace';

export const App: React.FC = () => {
  const [activeDoc, setActiveDoc] = useState<DocumentMetadata | null>(null);
  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-slate-50">
      <Navbar activeFilename={activeDoc?.filename} status={activeDoc?.status} />
      {activeDoc ? <DocumentWorkspace document={activeDoc} /> : (
        <div className="flex-1 overflow-auto p-6"><UploadView onUploadSuccess={setActiveDoc} /></div>
      )}
    </div>
  );
};

export default App;
