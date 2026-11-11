import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { SplitView } from './components/SplitView';
import { DocumentMetadata } from './types';
import { FileText } from 'lucide-react';
import { UploadView } from './views/UploadView';
import { DocumentChatPanel } from './components/chat/DocumentChatPanel';
import { DocumentSummaryPanel } from './components/summary/DocumentSummaryPanel';

export const App: React.FC = () => {
  const [activeDoc, setActiveDoc] = useState<DocumentMetadata | null>(null);

  const leftPanel = (
    <div className="flex-1 flex flex-col p-6 overflow-y-auto">
      {!activeDoc ? (
        <UploadView onUploadSuccess={setActiveDoc} />
      ) : (
        <div className="flex-1 flex flex-col space-y-4">
          <DocumentSummaryPanel documentId={activeDoc.id} filename={activeDoc.filename} />

          <DocumentChatPanel documentId={activeDoc.id} />
        </div>
      )}
    </div>
  );

  const rightPanel = (
    <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-slate-400">
      <div className="p-4 bg-white rounded-xl shadow-sm border border-slate-200 max-w-sm">
        <FileText className="w-10 h-10 text-slate-300 mx-auto mb-2" />
        <h3 className="text-sm font-medium text-slate-700">PDF Viewer Panel</h3>
        <p className="text-xs text-slate-400 mt-1">
          Embedded React-PDF / PDF.js viewer with citation highlight overlay scheduled for Stage 7.
        </p>
      </div>
    </div>
  );

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-slate-50">
      <Navbar activeFilename={activeDoc?.filename} status={activeDoc?.status} />
      <SplitView leftPanel={leftPanel} rightPanel={rightPanel} />
    </div>
  );
};

export default App;
