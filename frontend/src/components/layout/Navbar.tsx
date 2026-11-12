import { BookOpen, FileText, LayoutDashboard, UploadCloud } from 'lucide-react';
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
  return <header data-app-header className="z-10 w-full shrink-0 border-b border-slate-200 bg-white">
    <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-white focus:p-3 focus:text-blue-700">Skip to content</a>
    <div data-testid="navigation-container" className="mx-auto flex w-full min-w-0 max-w-[1440px] flex-col gap-3 px-4 py-3 sm:min-h-20 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
      <button type="button" onClick={() => onSelectTab('dashboard')} className="flex min-h-11 items-center gap-3 rounded-xl text-left">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white"><BookOpen size={21} aria-hidden="true" /></span>
        <span><span className="block text-base font-bold tracking-tight text-slate-900">ResearchAI</span><span className="block text-xs text-slate-500">Your research, connected</span></span>
      </button>
      <nav aria-label="Main Navigation" className="grid grid-flow-col auto-cols-fr gap-1 sm:flex">
        {ITEMS.filter(item => item.tab !== 'workspace' || activeDoc).map(({ tab, label, icon: Icon }) =>
          <button key={tab} type="button" onClick={() => onSelectTab(tab)} aria-current={activeTab === tab ? 'page' : undefined} className="ui-tab px-2 sm:px-4">
            <Icon size={17} aria-hidden="true" className="hidden sm:block" />{label}
          </button>)}
      </nav>
    </div>
  </header>;
}
