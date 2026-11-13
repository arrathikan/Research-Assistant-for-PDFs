import { useEffect, useId, useRef, useState, type KeyboardEvent } from 'react';
import { createPortal } from 'react-dom';
import { ArrowUpRight, FileText, MoreHorizontal, Trash2 } from 'lucide-react';
import type { DocumentMetadata } from '../../types';
import { api } from '../../services/api';

interface Props { document: DocumentMetadata; onOpen: () => void; onDelete?: () => void; }

export function DocumentActions({ document: paper, onOpen, onDelete }: Props) {
  const id = useId(), anchor = '--paper-actions-' + id.replace(/:/g, '');
  const trigger = useRef<HTMLButtonElement>(null), popup = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const nativePopover = 'popover' in HTMLElement.prototype;
  const nativeFocus = 'focusGroup' in HTMLElement.prototype;
  const nativeInvoker = 'commandForElement' in HTMLButtonElement.prototype;
  const anchored = typeof CSS !== 'undefined' && CSS.supports?.('position-area: block-end');
  const validId = !!paper.id && /^[0-9a-f]{24}$/i.test(paper.id);
  function items() { return Array.from(popup.current?.querySelectorAll<HTMLElement>('[data-paper-action]') ?? []); }
  function close(restore = true) {
    if (nativePopover && popup.current?.matches(':popover-open')) popup.current.hidePopover();
    setOpen(false); if (restore) trigger.current?.focus();
  }
  function position() {
    const menu = popup.current, button = trigger.current;
    if (!menu || !button || anchored && nativePopover) return;
    const b = button.getBoundingClientRect(), m = menu.getBoundingClientRect();
    menu.style.left = Math.max(16, Math.min(b.right - m.width, window.innerWidth - m.width - 16)) + 'px';
    menu.style.top = Math.max(16, b.bottom + m.height + 8 < window.innerHeight ? b.bottom + 8 : b.top - m.height - 8) + 'px';
  }
  function show() {
    if (nativePopover) popup.current?.showPopover();
    else { setOpen(true); requestAnimationFrame(() => { position(); items()[0]?.focus(); }); }
  }
  useEffect(() => {
    const menu = popup.current;
    trigger.current?.style.setProperty('anchor-name', anchor);
    menu?.style.setProperty('position-anchor', anchor);
    const toggle = (event: Event) => {
      const visible = (event as Event & { newState: string }).newState === 'open';
      setOpen(visible); if (visible) { position(); items()[0]?.focus(); }
    };
    menu?.addEventListener('toggle', toggle);
    return () => menu?.removeEventListener('toggle', toggle);
  }, [anchor]);
  useEffect(() => {
    if (!open) return;
    const outside = (event: PointerEvent) => {
      if (!nativePopover && !popup.current?.contains(event.target as Node) && !trigger.current?.contains(event.target as Node)) close(false);
    };
    const resized = () => close();
    window.addEventListener('pointerdown', outside); window.addEventListener('resize', resized);
    return () => { window.removeEventListener('pointerdown', outside); window.removeEventListener('resize', resized); };
  }, [open]);
  function keyboard(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'Escape') { event.preventDefault(); close(); return; }
    if (event.key === 'Tab') { close(); return; }
    if (nativeFocus || !['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault(); const controls = items(); const current = controls.indexOf(window.document.activeElement as HTMLElement);
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? controls.length - 1 : (current + (event.key === 'ArrowUp' ? -1 : 1) + controls.length) % controls.length;
    controls[next]?.focus();
  }
  const itemProps = { 'data-paper-action': '', role: nativeFocus ? undefined : 'menuitem', tabIndex: 0 };
  const menu = <div ref={popup} id={id} {...(nativePopover ? { popover: 'auto' } : { hidden: !open })} className="paper-actions-popup">
    <div {...{ focusgroup: 'menu nomemory' }} role={nativeFocus ? undefined : 'menu'} aria-label={'Actions for ' + paper.filename} onKeyDown={keyboard}>
      <button {...itemProps} type="button" className="ui-button ui-button-ghost ui-link w-full justify-start" onClick={() => { close(); onOpen(); }}><FileText size={16} aria-hidden="true" />Open Workspace</button>
      {validId && <a {...itemProps} className="ui-button ui-button-ghost ui-link w-full justify-start" href={api.getPdfStreamUrl(paper.id!)} target="_blank" rel="noreferrer" onClick={() => close()}><ArrowUpRight size={16} aria-hidden="true" />View Original PDF<span className="sr-only"> (opens in a new tab)</span></a>}
      {onDelete && <button {...itemProps} type="button" className="ui-button w-full justify-start text-red-700 hover:bg-red-50" onClick={() => { close(); onDelete(); }}><Trash2 size={16} aria-hidden="true" />Delete Paper</button>}
    </div>
  </div>;
  return <>
    <button ref={trigger} type="button" aria-label={'Paper actions for ' + paper.filename} aria-haspopup="menu" aria-controls={id} aria-expanded={open}
      {...(nativePopover && nativeInvoker ? { command: 'toggle-popover', commandfor: id } : {})}
      onClick={() => { if (!nativePopover || !nativeInvoker) { if (open) close(); else show(); } }}
      onKeyDown={event => { if (event.key === 'ArrowDown') { event.preventDefault(); show(); } }} className="ui-icon-button ui-button-ghost ml-auto"><MoreHorizontal size={20} aria-hidden="true" /></button>
    {nativePopover ? menu : createPortal(menu, window.document.body)}
  </>;
}
