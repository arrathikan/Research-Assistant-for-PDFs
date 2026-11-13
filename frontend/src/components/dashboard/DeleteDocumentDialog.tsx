import { useRef, useState } from 'react';
import { Loader2, Trash2 } from 'lucide-react';
import { Modal } from '../common/Modal';
import type { DocumentMetadata } from '../../types';
import { ApiError } from '../../services/api';

interface Props { document: DocumentMetadata; onCancel: () => void; onDelete: (document: DocumentMetadata) => Promise<void>; onDeleted: () => void; }
export function DeleteDocumentDialog({ document: paper, onCancel, onDelete, onDeleted }: Props) {
  const cancel = useRef<HTMLButtonElement>(null), inFlight = useRef(false);
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  async function confirm() {
    if (inFlight.current) return;
    inFlight.current = true; setBusy(true); setError('');
    try { await onDelete(paper); onDeleted(); }
    catch (failure: unknown) {
      setError(failure instanceof ApiError && failure.status === 409
        ? 'Your paper is saving data. Wait a moment, then try deleting it again.'
        : 'Deletion did not finish. The paper remains in your library. Retry deletion to finish removing its data.');
    } finally { inFlight.current = false; setBusy(false); }
  }
  return <Modal open title="Delete research paper?" description="This permanently removes the paper and its document-specific research data." busy={busy} initialFocus={cancel} onClose={onCancel} closeLabel="Close delete confirmation">
    <p className="break-words text-sm leading-7 text-stone-700 [overflow-wrap:anywhere]">Are you sure you want to delete <strong className="font-semibold">“{paper.filename}”</strong>?</p>
    <p className="mt-2 text-sm leading-6 text-stone-600">The original PDF, extracted content, summary and chat history will be removed. This cannot be undone.</p>
    {error && <p role="alert" className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm leading-6 text-red-800">{error}</p>}
    {busy && <p role="status" className="mt-4 text-sm text-stone-600">Deleting this paper. Please wait until cleanup is confirmed.</p>}
    <div className="mt-6 flex flex-wrap justify-end gap-2">
      <button ref={cancel} type="button" disabled={busy} onClick={onCancel} className="ui-button ui-button-secondary">Cancel</button>
      <button type="button" disabled={busy} onClick={() => void confirm()} className="ui-button ui-button-danger">{busy ? <Loader2 size={16} aria-hidden="true" className="motion-safe:animate-spin" /> : <Trash2 size={16} aria-hidden="true" />}{busy ? 'Deleting…' : 'Delete Paper'}</button>
    </div>
  </Modal>;
}
