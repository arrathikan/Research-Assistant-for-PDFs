import { FileText, LayoutDashboard, UploadCloud } from 'lucide-react';
import { BrandIdentity } from '../common/BrandIdentity';
import type { NavigationTab, DocumentMetadata } from '../../types';

interface NavbarProps {
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  activeDoc: DocumentMetadata | null;
}
const ITEMS = [
  { tab: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { tab: 'upload', label: 'Upload Paper', icon: UploadCloud },
  { tab: 'workspace', label: 'Workspace', icon: FileText },
] as const;

export function Navbar({ activeTab, onSelectTab, activeDoc }: NavbarProps) {
  return <>
    <header data-app-header className="app-header z-10 border-b border-stone-200 bg-white">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-white focus:p-3 focus:text-brand-700">Skip to content</a>
      <div data-testid="navigation-container" className="mx-auto flex w-full min-w-0 max-w-[1680px] items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <button type="button" aria-label="ResearchAI home" onClick={() => onSelectTab('dashboard')} className="flex min-h-11 items-center rounded-lg text-left"><BrandIdentity /></button>
        <span className="hidden text-xs text-stone-500 sm:block">Your research, clearly connected.</span>
      </div>
    </header>
    <aside data-app-navigation className="app-sidebar border-b border-stone-200 bg-white p-2 sm:px-4 xl:border-b-0 xl:border-r xl:px-4 xl:py-6">
      <nav aria-label="Main Navigation" className="grid grid-cols-3 gap-1 xl:grid-cols-1 xl:gap-2">
        {ITEMS.map(({ tab, label, icon: Icon }) => <button key={tab} type="button"
          disabled={tab === 'workspace' && !activeDoc} onClick={() => onSelectTab(tab)}
          aria-current={activeTab === tab ? 'page' : undefined} className="ui-tab px-2 xl:justify-start xl:px-4">
          <Icon size={19} aria-hidden="true" className="hidden sm:block" />{label}
        </button>)}
      </nav>
      <p className="mt-8 hidden border-t border-stone-200 px-3 pt-4 text-xs leading-5 text-stone-500 xl:block">Upload a paper to explore its summary and ask questions with sources.</p>
    </aside>
  </>;
}
