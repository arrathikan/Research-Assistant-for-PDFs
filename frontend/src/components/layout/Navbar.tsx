import React from 'react';
import { BookOpen, UploadCloud, LayoutDashboard, FileText, ChevronRight } from 'lucide-react';
import { NavigationTab, DocumentMetadata } from '../../types';

interface NavbarProps {
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  activeDoc: DocumentMetadata | null;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onSelectTab,
  activeDoc,
}) => {
  return (
    <header className="flex shrink-0 flex-col gap-3 border-b border-slate-200 bg-white px-4 py-3 shadow-2xs z-10 sm:h-16 sm:flex-row sm:items-center sm:justify-between sm:px-6 sm:py-0">
      {/* Brand & Breadcrumb */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => onSelectTab('dashboard')}
          className="flex items-center gap-2.5 text-left group rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2"
        >
          <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-sm group-hover:bg-blue-700 transition-colors">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-bold text-slate-900 leading-none">ResearchAI</div>
            <div className="text-[11px] text-slate-500 font-medium mt-0.5">Academic Paper Assistant</div>
          </div>
        </button>

        {activeDoc && activeTab !== 'upload' && (
          <div className="hidden xl:flex items-center gap-2 text-xs text-slate-400 pl-3 border-l border-slate-200">
            <ChevronRight className="w-4 h-4 text-slate-300" />
            <span className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 rounded-md text-slate-700 font-medium truncate max-w-xs">
              <FileText className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" />
              <span className="truncate">{activeDoc.filename}</span>
            </span>
            <span
              data-testid="document-status-pill"
              className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${
                activeDoc.status === 'READY'
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : activeDoc.status === 'FAILED'
                  ? 'bg-rose-50 text-rose-700 border border-rose-200'
                  : 'bg-amber-50 text-amber-700 border border-amber-200 animate-pulse'
              }`}
            >
              {activeDoc.status}
            </span>
          </div>
        )}
      </div>

      {/* Navigation Controls */}
      <nav aria-label="Main Navigation" className="grid w-full grid-flow-col auto-cols-fr items-center gap-1 rounded-xl border border-slate-200 bg-slate-100 p-1 sm:flex sm:w-auto">
        <button
          onClick={() => onSelectTab('dashboard')}
          className={`flex min-h-11 items-center justify-center gap-1.5 whitespace-nowrap px-2 py-1.5 rounded-lg text-xs font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 sm:px-3 ${
            activeTab === 'dashboard'
              ? 'bg-white text-blue-700 shadow-2xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
          }`}
        >
          <LayoutDashboard aria-hidden="true" className="hidden h-4 w-4 shrink-0 sm:block" />
          <span>Dashboard</span>
        </button>

        <button
          onClick={() => onSelectTab('upload')}
          className={`flex min-h-11 items-center justify-center gap-1.5 whitespace-nowrap px-2 py-1.5 rounded-lg text-xs font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 sm:px-3 ${
            activeTab === 'upload'
              ? 'bg-white text-blue-700 shadow-2xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
          }`}
        >
          <UploadCloud aria-hidden="true" className="hidden h-4 w-4 shrink-0 sm:block" />
          <span>Upload Paper</span>
        </button>

        {activeDoc && (
          <button
            onClick={() => onSelectTab('workspace')}
            className={`flex min-h-11 items-center justify-center gap-1.5 whitespace-nowrap px-2 py-1.5 rounded-lg text-xs font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 sm:px-3 ${
              activeTab === 'workspace'
                ? 'bg-white text-blue-700 shadow-2xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
            }`}
          >
            <FileText aria-hidden="true" className="hidden h-4 w-4 shrink-0 sm:block" />
            <span>Workspace</span>
          </button>
        )}
      </nav>
    </header>
  );
};
