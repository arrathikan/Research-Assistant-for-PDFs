import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { SplitView } from './components/SplitView';
import { DocumentMetadata } from './types';
import { UploadCloud, MessageSquare, FileText } from 'lucide-react';

export const App: React.FC = () => {
  const [activeDoc, setActiveDoc] = useState<DocumentMetadata | null>(null);

  const leftPanel = (
    <div className="flex-1 flex flex-col p-6 overflow-y-auto">
      {!activeDoc ? (
        <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-slate-300 rounded-xl p-8 text-center bg-slate-50">
          <div className="p-4 bg-blue-50 text-blue-600 rounded-full mb-4">
            <UploadCloud className="w-8 h-8" />
          </div>
          <h2 className="text-base font-semibold text-slate-800">Upload Academic Research PDF</h2>
          <p className="text-xs text-slate-500 max-w-sm mt-1">
            Drag and drop a research paper or browse files. Generates a structured 5-part summary and opens conversational Hybrid RAG.
          </p>
          <button
            onClick={() => {
              // Simulated upload placeholder for Stage 1 layout verification
              setActiveDoc({
                sha256: 'simulated_hash',
                filename: 'sample_paper.pdf',
                file_size_bytes: 1200000,
                status: 'READY',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              });
            }}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
          >
            Select PDF Document
          </button>
        </div>
      ) : (
        <div className="flex-1 flex flex-col space-y-4">
          <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
            <div className="flex items-center gap-2 text-slate-700 text-sm font-semibold">
              <FileText className="w-4 h-4 text-blue-600" />
              <span>Structured Summary (5 Sections)</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Summary will be generated via LangGraph deterministic workflow in Stage 5.
            </p>
          </div>

          <div className="flex-1 p-4 bg-slate-50 rounded-lg border border-slate-200 flex flex-col justify-between">
            <div className="flex items-center gap-2 text-slate-700 text-sm font-semibold">
              <MessageSquare className="w-4 h-4 text-emerald-600" />
              <span>Hybrid RAG Chat</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Conversational QA with jump-to-citation PDF highlighting scheduled for Stage 6.
            </p>
          </div>
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
