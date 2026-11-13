import { useId } from 'react';
import { MessageSquare, BookOpen } from 'lucide-react';
import type { DocumentMetadata } from '../../types';
import { DocumentActions } from './DocumentActions';
import { DocumentStatusBadge } from '../common/DocumentStatusBadge';
import { ResearchArtwork } from '../common/ResearchArtwork';
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
  const summaryReady = document.status === 'READY';
  const chatReady = summaryReady || document.embedding_status === 'COMPLETED';
  return <tr data-testid="document-card" className="research-paper-card">
    <th scope="row" className="paper-name">
      <div className="flex min-w-0 items-center gap-2.5">
        <ResearchArtwork kind="paper" className="h-11 w-11" />
        <button id={titleId} type="button" onClick={() => onOpen(document)} className="min-w-0 rounded text-left text-sm font-semibold leading-5 text-stone-900 hover:text-brand-700 [overflow-wrap:anywhere]">{document.filename}</button>
      </div>
    </th>
    <td data-label="Size" className="text-xs text-stone-600">{formatFileSize(document.file_size_bytes)}</td>
    <td data-label="Uploaded" className="text-xs text-stone-600"><span className="sr-only">Uploaded </span><time dateTime={document.created_at}>{date}</time></td>
    <td data-label="Status"><DocumentStatusBadge status={document.status} /></td>
    <td className="paper-actions"><div className="flex flex-wrap items-center gap-1">
      {onViewSummary && <button type="button" disabled={!summaryReady} aria-describedby={titleId} onClick={() => onViewSummary(document)} className="ui-button ui-document-action px-2 text-xs"><BookOpen size={15} aria-hidden="true" />Summary</button>}
      {onOpenChat && <button type="button" disabled={!chatReady} aria-describedby={titleId} onClick={() => onOpenChat(document)} className="ui-button ui-document-action px-2 text-xs"><MessageSquare size={15} aria-hidden="true" />Chat</button>}
      <DocumentActions document={document} onOpen={() => onOpen(document)} onDelete={onDelete ? () => onDelete(document) : undefined} />
    </div></td>
  </tr>;
}
