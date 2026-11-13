import researchaiLogo from '../../assets/researchai-logo.png';

/** Keep the supplied book artwork, with one legible wordmark at compact header sizes. */
export function BrandIdentity() {
  return <span className="flex min-w-0 items-center gap-2.5">
    <svg data-testid="brand-logo" aria-hidden="true" focusable="false" viewBox="250 170 750 750" className="h-11 w-11 shrink-0">
      <image href={researchaiLogo} width={1254} height={1254} />
    </svg>
    <span className="min-w-0 text-left">
      <span className="block text-xl font-semibold tracking-tight text-stone-900">Research<span className="text-brand-600">AI</span></span>
      <span className="block text-[11px] text-stone-600">Academic Paper Assistant</span>
    </span>
  </span>;
}
