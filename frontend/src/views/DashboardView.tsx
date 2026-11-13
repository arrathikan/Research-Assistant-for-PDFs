import React, { useRef, useState } from 'react';
import { DocumentMetadata, WorkspaceTab } from '../types';
import { DeleteDocumentDialog } from '../components/dashboard/DeleteDocumentDialog';
import { DocumentCard } from '../components/dashboard/DocumentCard';
import { EmptyState } from '../components/common/EmptyState';
import { Search, UploadCloud } from 'lucide-react';

import { PageContainer } from '../components/layout/PageContainer';
interface DashboardViewProps {
  documents: DocumentMetadata[];
  onSelectDocument: (doc: DocumentMetadata, tab?: WorkspaceTab) => void;
  onNavigateUpload: () => void;
  onDeleteDocument?: (doc: DocumentMetadata) => Promise<void>;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  documents,
  onSelectDocument,
  onNavigateUpload,
  onDeleteDocument,
}) => {
  const [deleting, setDeleting] = useState<DocumentMetadata | null>(null);
  const [notice, setNotice] = useState('');
  const heading = useRef<HTMLHeadingElement>(null);
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
      {/* Library heading and primary action. */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <p className="ui-eyebrow mb-2">Your research</p>
          <h1 ref={heading} tabIndex={-1} className="ui-page-title">Paper Library</h1>
          <p className="mt-2 text-sm leading-6 text-stone-600">
            Read, understand and return to the papers that matter to your research.
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

      {notice && <p role="status" className="mb-4 text-sm text-stone-600">{notice}</p>}
      <section aria-label="Library statistics" className="mb-7 flex flex-wrap gap-x-8 gap-y-3 border-y border-stone-200 py-4 text-sm text-stone-600">
        <div className="flex items-baseline gap-2"><strong className="font-semibold tabular-nums text-stone-900">{documents.length}</strong><span>Total Research Papers</span></div>
        <div className="flex items-baseline gap-2"><strong className="font-semibold tabular-nums text-stone-900">{readyCount}</strong><span>Ready to explore</span></div>
        <div className="flex items-baseline gap-2"><strong className="font-semibold tabular-nums text-stone-900">{formattedStorage}</strong><span>PDF Storage</span></div>
      </section>

      <h2 className="mb-4 text-lg font-semibold tracking-tight text-stone-900">Your papers</h2>

      {/* Search & Filter Bar */}
      {documents.length > 0 && (
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div className="relative w-full sm:max-w-md">
            <Search aria-hidden="true" className="w-4 h-4 text-stone-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="search"
              aria-label="Search papers"
              placeholder="Search by filename"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="ui-field w-full pl-10"
            />
          </div>
          <span className="shrink-0 text-sm text-stone-500">
            Showing {filteredDocuments.length} of {documents.length}
          </span>
        </div>
      )}

      {/* Research library or an actionable empty state. */}
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
        <section aria-label="Research papers" className="paper-library min-w-0 divide-y divide-stone-200 rounded-xl border border-stone-200 bg-white">
          {filteredDocuments.map((doc) => (
            <DocumentCard
              key={doc.sha256}
              document={doc}
              onOpen={onSelectDocument}
              onDelete={onDeleteDocument ? document => { setNotice(''); setDeleting(document); } : undefined}
              onViewSummary={doc => onSelectDocument(doc, 'summary')}
              onOpenChat={doc => onSelectDocument(doc, 'chat')}
            />
          ))}
        </section>
      )}
      {deleting && onDeleteDocument && <DeleteDocumentDialog key={deleting.id} document={deleting} onDelete={onDeleteDocument} onCancel={() => setDeleting(null)}
        onDeleted={() => { setDeleting(null); setNotice('Paper deleted. Your library is up to date.'); requestAnimationFrame(() => heading.current?.focus()); }} />}
    </PageContainer>
  );
};
