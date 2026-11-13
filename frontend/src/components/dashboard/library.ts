import type { DocumentMetadata, DocumentStatus } from '../../types';

export type LibraryFilter = 'all' | 'ready' | 'processing' | 'uploaded' | 'failed';
export type LibrarySort = 'newest' | 'oldest' | 'name';
export const isProcessingStatus = (status: DocumentStatus) =>
  status === 'PARSING' || status === 'EMBEDDING' || status === 'SUMMARIZING';
const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });

export function visiblePapers(documents: DocumentMetadata[], query: string, filter: LibraryFilter, sort: LibrarySort) {
  return documents.filter(doc => doc.filename.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()))
    .filter(doc => filter === 'all' || (filter === 'ready' && doc.status === 'READY')
      || (filter === 'processing' && isProcessingStatus(doc.status))
      || (filter === 'uploaded' && doc.status === 'PENDING') || (filter === 'failed' && doc.status === 'FAILED'))
    .sort((a, b) => sort === 'name' ? collator.compare(a.filename, b.filename)
      : (Date.parse(a.created_at) - Date.parse(b.created_at)) * (sort === 'oldest' ? 1 : -1));
}
