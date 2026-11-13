import researchaiLogo from '../../assets/researchai-logo.png';

/** The supplied logo is used unchanged; text keeps the brand readable at small sizes. */
export function BrandIdentity() {
  return <span className="flex min-w-0 items-center gap-3">
    <img data-testid="brand-logo" src={researchaiLogo}
      alt="" width={1254} height={1254} className="h-12 w-14 shrink-0 object-contain" />
    <span className="min-w-0 text-left">
      <span className="block text-lg font-semibold tracking-tight text-stone-900">ResearchAI</span>
      <span className="block text-xs text-stone-600">Academic Paper Assistant</span>
    </span>
  </span>;
}
