import { useId } from 'react';
import { FileText, MessageSquare, BookOpen } from 'lucide-react';
import type { DocumentMetadata } from '../../types';
import { DocumentActions } from './DocumentActions';
import { DocumentStatusBadge } from '../common/DocumentStatusBadge';
import { formatFileSize } from '../upload/formatFileSize';

interface DocumentCardProps {
  document: DocumentMetadata;
  onOpen: (doc: DocumentMetadata) => void;
  onViewSummary?: (doc: DocumentMetadata) => void;
  onOpenChat?: (doc: DocumentMetadata) => void;
  onDelete?: (doc: DocumentMetadata) => void;
}

export function DocumentCard({ document, onOpen, onViewSummary, onOpenChat, onDelete }: DocumentCardProps) {
  const titleId = useId();
  const date = new Date(document.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  return <article data-testid="document-card" className="research-paper-card">
    <FileText size={44} aria-hidden="true" className="paper-card-icon rounded-lg bg-stone-100 p-2.5 text-stone-600" />
    <header className="paper-card-header flex min-w-0 flex-wrap items-center gap-3">
      <h3 id={titleId} className="min-w-0 text-base font-semibold leading-6 text-stone-900 [overflow-wrap:anywhere]">
        <button type="button" onClick={() => onOpen(document)} className="rounded text-left hover:text-brand-700">{document.filename}</button>
      </h3>
      <DocumentStatusBadge status={document.status} />
    </header>
    <p className="paper-card-meta flex flex-wrap items-center gap-x-3 gap-y-1 text-xs leading-5 text-stone-500">
      <span>{formatFileSize(document.file_size_bytes)}</span>
      <span>Uploaded <time dateTime={document.created_at}>{date}</time></span>
    </p>
    <footer className="paper-card-actions">
      <div className="flex items-center gap-1">
        {onViewSummary && <button type="button" aria-describedby={titleId} onClick={() => onViewSummary(document)} className="ui-button ui-button-ghost px-2 text-xs"><BookOpen size={15} aria-hidden="true" />Summary</button>}
        {onOpenChat && <button type="button" aria-describedby={titleId} onClick={() => onOpenChat(document)} className="ui-button ui-button-ghost px-2 text-xs"><MessageSquare size={15} aria-hidden="true" />Chat</button>}
      </div>
      <DocumentActions document={document} onOpen={() => onOpen(document)} onDelete={onDelete ? () => onDelete(document) : undefined} />
    </footer>
  </article>;
}
