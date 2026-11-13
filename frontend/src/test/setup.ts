import "@testing-library/jest-dom/vitest";

// JSDOM has no native dialog implementation. Model only the browser methods;
// focus containment, Escape and top-layer behavior are verified in a real browser.
if (!HTMLDialogElement.prototype.showModal) {
  const previousFocus = new WeakMap<HTMLDialogElement, HTMLElement | null>();
  HTMLDialogElement.prototype.showModal = function () {
    previousFocus.set(this, document.activeElement as HTMLElement | null);
    this.setAttribute('open', '');
    this.querySelector<HTMLElement>('button:not([disabled]), input:not([hidden])')?.focus();
  };
  HTMLDialogElement.prototype.close = function () {
    this.removeAttribute('open');
    previousFocus.get(this)?.focus();
    this.dispatchEvent(new Event('close'));
    // React's selection restoration can focus a closed dialog in JSDOM only.
    queueMicrotask(() => { if (!this.open) previousFocus.get(this)?.focus(); });
  };
}
