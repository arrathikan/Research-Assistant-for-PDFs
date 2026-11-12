import React, { useState } from 'react';
import { DocumentMetadata, WorkspaceTab } from '../types';
import { DocumentCard } from '../components/dashboard/DocumentCard';
import { EmptyState } from '../components/common/EmptyState';
import { BookOpen, Search, UploadCloud, Layers, Database } from 'lucide-react';

import { PageContainer } from '../components/layout/PageContainer';
interface DashboardViewProps {
  documents: DocumentMetadata[];
  onSelectDocument: (doc: DocumentMetadata, tab?: WorkspaceTab) => void;
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
    <PageContainer>
      {/* Top Banner & Stats */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <p className="ui-eyebrow mb-2">Your research</p>
          <h1 className="ui-page-title">Paper Library</h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            A home for your papers, their key ideas and your next question.
          </p>
        </div>

        <button
          onClick={onNavigateUpload}
          className="ui-button ui-button-primary self-start md:self-auto"
        >
          <UploadCloud aria-hidden="true" className="w-4 h-4" />
          <span>Upload Paper</span>
        </button>
      </div>

      {/* Metrics Bar */}
      <section aria-label="Library statistics" className="grid min-w-0 grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="ui-card flex items-center gap-4 p-5">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
            <BookOpen aria-hidden="true" className="w-5 h-5" />
          </div>
          <div>
            <div className="text-2xl font-semibold tracking-tight text-slate-900">{documents.length}</div>
            <div className="text-sm text-slate-500">Total Research Papers</div>
          </div>
        </div>

        <div className="ui-card flex items-center gap-4 p-5">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
            <Layers aria-hidden="true" className="w-5 h-5" />
          </div>
          <div>
            <div className="text-2xl font-semibold tracking-tight text-slate-900">{readyCount}</div>
            <div className="text-sm text-slate-500">Ready to explore</div>
          </div>
        </div>

        <div className="ui-card flex items-center gap-4 p-5">
          <div className="p-3 bg-slate-100 text-slate-600 rounded-xl">
            <Database aria-hidden="true" className="w-5 h-5" />
          </div>
          <div>
            <div className="text-2xl font-semibold tracking-tight text-slate-900">{formattedStorage}</div>
            <div className="text-sm text-slate-500">PDF Storage</div>
          </div>
        </div>
      </section>

      <h2 className="mb-4 mt-8 text-lg font-semibold tracking-tight text-slate-900">Your papers</h2>

      {/* Search & Filter Bar */}
      {documents.length > 0 && (
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div className="relative w-full sm:max-w-md">
            <Search aria-hidden="true" className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              aria-label="Search papers"
              placeholder="Search papers by filename..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="ui-field w-full pl-10"
            />
          </div>
          <span className="shrink-0 text-sm text-slate-500">
            Showing {filteredDocuments.length} of {documents.length}
          </span>
        </div>
      )}

      {/* Document Grid or Empty State */}
      {documents.length === 0 ? (
        <div className="py-4">
          <EmptyState
            title="No research papers uploaded yet"
            description="Start with one PDF. We’ll organize its key ideas and help you explore questions with sources."
            action={
              <button
                onClick={onNavigateUpload}
                className="ui-button ui-button-primary"
              >
                <UploadCloud aria-hidden="true" className="w-4 h-4" />
                <span>Upload First Paper</span>
              </button>
            }
          />
        </div>
      ) : filteredDocuments.length === 0 ? (
        <div className="py-4">
          <EmptyState
            title="No matching papers found"
            description={`No uploaded document matches the query "${searchQuery}".`}
          />
        </div>
      ) : (
        <section aria-label="Research papers" className="grid min-w-0 grid-cols-[repeat(auto-fit,minmax(min(100%,20rem),1fr))] gap-5">
          {filteredDocuments.map((doc) => (
            <DocumentCard
              key={doc.sha256}
              document={doc}
              onOpen={onSelectDocument}
              onViewSummary={doc => onSelectDocument(doc, 'summary')}
              onOpenChat={doc => onSelectDocument(doc, 'chat')}
            />
          ))}
        </section>
      )}
    </PageContainer>
  );
};
