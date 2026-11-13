import React, { useRef, useState } from 'react';
import { Search, UploadCloud, FolderOpen, Database, X } from 'lucide-react';
import { DocumentMetadata, WorkspaceTab } from '../types';
import { DeleteDocumentDialog } from '../components/dashboard/DeleteDocumentDialog';
import { DocumentCard } from '../components/dashboard/DocumentCard';
import { isProcessingStatus, visiblePapers, type LibraryFilter, type LibrarySort } from '../components/dashboard/library';
import { EmptyState } from '../components/common/EmptyState';
import { ResearchArtwork, type ResearchArtworkKind } from '../components/common/ResearchArtwork';
import { PageContainer } from '../components/layout/PageContainer';
import { formatFileSize } from '../components/upload/formatFileSize';

interface DashboardViewProps {
  documents: DocumentMetadata[];
  onSelectDocument: (doc: DocumentMetadata, tab?: WorkspaceTab) => void;
  onNavigateUpload: () => void;
  onDeleteDocument?: (doc: DocumentMetadata) => Promise<void>;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ documents, onSelectDocument, onNavigateUpload, onDeleteDocument }) => {
  const [deleting, setDeleting] = useState<DocumentMetadata | null>(null);
  const [notice, setNotice] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<LibraryFilter>('all');
  const [sort, setSort] = useState<LibrarySort>('newest');
  const heading = useRef<HTMLHeadingElement>(null), search = useRef<HTMLInputElement>(null);
  const filteredDocuments = visiblePapers(documents, searchQuery, filter, sort);
  const latest = visiblePapers(documents, '', 'all', 'newest')[0];
  const metrics: { label: string; value: string | number; artwork?: ResearchArtworkKind }[] = [
    { label: 'Total Papers', value: documents.length, artwork: 'paper' },
    { label: 'Ready to Explore', value: documents.filter(doc => doc.status === 'READY').length, artwork: 'ready' },
    { label: 'Processing', value: documents.filter(doc => isProcessingStatus(doc.status)).length, artwork: 'processing' },
    { label: 'Storage Used', value: formatFileSize(documents.reduce((sum, doc) => sum + doc.file_size_bytes, 0)) },
  ];
  return <PageContainer>
    <section className="library-welcome mb-5 flex min-w-0 items-center justify-between gap-4 rounded-2xl border border-brand-200 bg-brand-50 px-5 py-6 sm:px-7" aria-labelledby="library-heading">
      <div className="min-w-0">
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-brand-700">Welcome to ResearchAI</p>
        <h1 id="library-heading" ref={heading} tabIndex={-1} className="ui-page-title">Paper Library</h1>
        <p className="mt-2 max-w-xl text-sm leading-6 text-stone-600">Upload, explore and understand your research papers with AI.</p>
        <div className="mt-5 flex flex-wrap gap-2.5">
          <button type="button" onClick={onNavigateUpload} className="ui-button ui-button-primary"><UploadCloud size={17} aria-hidden="true" />Upload Paper</button>
          <button type="button" disabled={!latest} onClick={() => latest && onSelectDocument(latest, 'summary')} className="ui-button ui-button-secondary"><FolderOpen size={17} aria-hidden="true" />Open Workspace</button>
        </div>
      </div>
      <ResearchArtwork kind="hero" className="hidden h-36 w-72 max-w-[32%] lg:block" />
    </section>
    {notice && <p role="status" className="mb-4 text-sm text-stone-600">{notice}</p>}
    <section aria-label="Library statistics" className="mb-7 grid grid-cols-2 gap-3 lg:grid-cols-4">
      {metrics.map(metric => <div key={metric.label} className="ui-card flex min-w-0 items-center gap-3 p-4">
        {metric.artwork ? <ResearchArtwork kind={metric.artwork} className="h-12 w-12" /> : <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-stone-100 text-stone-600"><Database size={24} aria-hidden="true" /></span>}
        <div className="min-w-0"><strong className="block text-xl font-semibold tabular-nums leading-7 text-stone-900 sm:text-2xl">{metric.value}</strong><span className="block text-xs leading-5 text-stone-600">{metric.label}</span></div>
      </div>)}
    </section>
    <h2 className="mb-3 text-lg font-semibold tracking-tight text-stone-900">Your papers</h2>
    {documents.length > 0 && <>
      <div className="library-filters mb-3 grid min-w-0 gap-3 md:grid-cols-[minmax(0,1fr)_auto_auto]">
        <div className="relative min-w-0">
          <Search aria-hidden="true" className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-500" />
          <input ref={search} type="search" aria-label="Search papers" placeholder="Search by filename" value={searchQuery} onChange={event => setSearchQuery(event.target.value)} className="ui-field w-full pl-10 pr-11" />
          {searchQuery && <button type="button" aria-label="Clear search" onClick={() => { setSearchQuery(''); search.current?.focus(); }} className="absolute right-1 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-md text-stone-500 hover:bg-stone-100"><X size={16} aria-hidden="true" /></button>}
        </div>
        <label className="min-w-0"><span className="sr-only">Filter by status</span><select className="ui-field w-full text-sm" value={filter} onChange={event => setFilter(event.target.value as LibraryFilter)}>
          <option value="all">All statuses</option><option value="ready">Ready</option><option value="processing">Processing</option><option value="uploaded">Uploaded / Queued</option><option value="failed">Failed</option>
        </select></label>
        <label className="min-w-0"><span className="sr-only">Sort papers</span><select className="ui-field w-full text-sm" value={sort} onChange={event => setSort(event.target.value as LibrarySort)}>
          <option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="name">Filename A–Z</option>
        </select></label>
      </div>
      <p role="status" className="mb-3 text-xs text-stone-500">Showing {filteredDocuments.length} of {documents.length} papers</p>
    </>}
    {documents.length === 0 ? <EmptyState title="No research papers uploaded yet" description="Start with one PDF. We’ll organize its key ideas and help you explore questions with sources." action={<button type="button" onClick={onNavigateUpload} className="ui-button ui-button-primary"><UploadCloud size={17} aria-hidden="true" />Upload First Paper</button>} />
      : filteredDocuments.length === 0 ? <EmptyState title="No matching papers found" description="Try a different filename or status filter." />
      : <section aria-label="Research papers" className="paper-library ui-card">
        <table className="paper-table"><caption className="sr-only">Your uploaded research papers</caption>
          <thead><tr><th scope="col" aria-sort={sort === 'name' ? 'ascending' : undefined}>Paper</th><th scope="col">Size</th><th scope="col" aria-sort={sort === 'name' ? undefined : sort === 'oldest' ? 'ascending' : 'descending'}>Uploaded</th><th scope="col">Status</th><th scope="col">Actions</th></tr></thead>
          <tbody>{filteredDocuments.map(doc => <DocumentCard key={doc.sha256} document={doc} onOpen={onSelectDocument}
            onDelete={onDeleteDocument ? document => { setNotice(''); setDeleting(document); } : undefined}
            onViewSummary={document => onSelectDocument(document, 'summary')} onOpenChat={document => onSelectDocument(document, 'chat')} />)}</tbody>
        </table>
      </section>}
    {deleting && onDeleteDocument && <DeleteDocumentDialog key={deleting.id} document={deleting} onDelete={onDeleteDocument} onCancel={() => setDeleting(null)} onDeleted={() => { setDeleting(null); setNotice('Paper deleted. Your library is up to date.'); requestAnimationFrame(() => heading.current?.focus()); }} />}
  </PageContainer>;
};
