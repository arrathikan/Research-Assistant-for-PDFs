import { useLayoutEffect, useId, useRef, type ReactNode, type RefObject } from 'react';
import { X } from 'lucide-react';

interface Props {
  open: boolean; title: string; description: string; children: ReactNode;
  onClose: () => void; busy?: boolean; closeLabel?: string;
  initialFocus?: RefObject<HTMLButtonElement>;
}

/** Native modal supplies the top layer, inert background, focus containment and return. */
export function Modal({ open, title, description, children, onClose, busy = false, closeLabel = 'Close dialog', initialFocus }: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId(), descriptionId = useId();
  useLayoutEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (open && !element.open) { element.showModal(); initialFocus?.current?.focus(); }
    else if (!open && element.open) element.close();
    return () => { if (element.open) element.close(); };
  }, [open, initialFocus]);
  return <dialog ref={dialog} aria-labelledby={titleId} aria-describedby={descriptionId}
    {...{ closedby: busy ? 'none' : 'closerequest' }} className="research-dialog ui-card"
    onCancel={event => { if (busy) event.preventDefault(); }}
    onClose={() => {
      if (dialog.current?.open) return; // Ignore a queued close event after reopening.
      if (busy) dialog.current?.showModal(); else onClose();
    }}>
    <header className="flex items-start justify-between gap-4 border-b border-stone-200 p-5 sm:p-6">
      <div><h2 id={titleId} className="text-lg font-semibold text-stone-900">{title}</h2><p id={descriptionId} className="mt-1 text-sm leading-6 text-stone-600">{description}</p></div>
      <button type="button" onClick={onClose} disabled={busy} aria-label={closeLabel} className="ui-icon-button ui-button-ghost"><X size={19} aria-hidden="true" /></button>
    </header>
    <div className="p-5 sm:p-6">{children}</div>
  </dialog>;
}
