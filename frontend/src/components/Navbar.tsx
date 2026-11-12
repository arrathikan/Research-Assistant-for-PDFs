import React from 'react';
import { BookOpen, FileText } from 'lucide-react';
import { DocumentStatusBadge } from './common/DocumentStatusBadge';
import type { DocumentStatus } from '../types';

interface NavbarProps {
  activeFilename?: string;
  status?: DocumentStatus;
}

export const Navbar: React.FC<NavbarProps> = ({ activeFilename, status }) => {
  return (
    <header data-app-header className="w-full shrink-0 border-b border-slate-200 bg-white">
      <div data-testid="navigation-container" className="mx-auto flex min-w-0 w-full flex-wrap items-center justify-between gap-3 px-4 py-3 sm:min-h-16 sm:flex-nowrap sm:px-6 lg:px-8 max-w-[1440px]">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-600 rounded-lg text-white">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <p className="text-base font-bold tracking-tight text-slate-900">ResearchAI</p>
            <p className="text-xs text-slate-500">Your research, connected</p>
          </div>
        </div>

        <div className="hidden min-w-0 items-center gap-4 sm:flex">
          {activeFilename ? (
            <div className="flex min-w-0 items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-md border border-slate-200 text-xs text-slate-700">
              <FileText className="w-4 h-4 text-slate-500" />
              <span className="font-medium truncate max-w-[12rem] lg:max-w-xs">{activeFilename}</span>
              {status && <DocumentStatusBadge status={status} />}
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">

              <span>Upload a research PDF to begin</span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
