import React, { useState } from 'react';
import { DocumentMetadata } from '../types';
import { DocumentCard } from '../components/dashboard/DocumentCard';
import { EmptyState } from '../common/EmptyState';
import { BookOpen, Search, UploadCloud, Layers, Database } from 'lucide-react';

interface DashboardViewProps {
  documents: DocumentMetadata[];
  onSelectDocument: (doc: DocumentMetadata) => void;
  onNavigateUpload: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  documents,
  onSelectDocument,
  onNavigateUpload,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredDocuments = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalBytes = documents.reduce((sum, d) => sum + d.file_size_bytes, 0);
  const formattedStorage =
    totalBytes < 1024 * 1024
      ? `${(totalBytes / 1024).toFixed(1)} KB`
      : `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;

  const readyCount = documents.filter((d) => d.status === 'READY').length;

  return (
    <div className="flex-1 overflow-y-auto p-8 max-w-7xl mx-auto w-full">
      {/* Top Banner & Stats */}
      <div className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Paper Library</h2>
          <p className="text-xs text-slate-500 mt-1">
            Manage your analyzed research papers and query them with Hybrid RAG.
          </p>
        </div>

        <button
          onClick={onNavigateUpload}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-colors self-start md:self-auto"
        >
          <UploadCloud className="w-4 h-4" />
          <span>Upload Paper</span>
        </button>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="p-4 bg-white rounded-2xl border border-slate-200 flex items-center gap-3.5 shadow-2xs">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-slate-900">{documents.length}</div>
            <div className="text-xs text-slate-400 font-medium">Total Research Papers</div>
          </div>
        </div>

        <div className="p-4 bg-white rounded-2xl border border-slate-200 flex items-center gap-3.5 shadow-2xs">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-slate-900">{readyCount}</div>
            <div className="text-xs text-slate-400 font-medium">Ready for Chat & RAG</div>
          </div>
        </div>

        <div className="p-4 bg-white rounded-2xl border border-slate-200 flex items-center gap-3.5 shadow-2xs">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-xl">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-slate-900">{formattedStorage}</div>
            <div className="text-xs text-slate-400 font-medium">Indexed PDF Storage</div>
          </div>
        </div>
      </div>

      {/* Search & Filter Bar */}
      {documents.length > 0 && (
        <div className="mb-6 flex items-center justify-between">
          <div className="relative w-full max-w-sm">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search papers by filename..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-xs placeholder:text-slate-400 focus:outline-hidden focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            />
          </div>
          <span className="text-xs text-slate-400 font-medium ml-4">
            Showing {filteredDocuments.length} of {documents.length}
          </span>
        </div>
      )}

      {/* Document Grid or Empty State */}
      {documents.length === 0 ? (
        <div className="py-16">
          <EmptyState
            title="No research papers uploaded yet"
            description="Upload an academic research PDF to generate a structured 5-part summary and chat with the document."
            action={
              <button
                onClick={onNavigateUpload}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-colors"
              >
                <UploadCloud className="w-4 h-4" />
                <span>Upload First Paper</span>
              </button>
            }
          />
        </div>
      ) : filteredDocuments.length === 0 ? (
        <div className="py-16">
          <EmptyState
            title="No matching papers found"
            description={`No uploaded document matches the query "${searchQuery}".`}
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredDocuments.map((doc) => (
            <DocumentCard
              key={doc.sha256}
              document={doc}
              onOpen={onSelectDocument}
              onViewSummary={onSelectDocument}
              onOpenChat={onSelectDocument}
            />
          ))}
        </div>
      )}
    </div>
  );
};
