import React from 'react';
import { FileText } from 'lucide-react';
import { BrandIdentity } from './common/BrandIdentity';
import { DocumentStatusBadge } from './common/DocumentStatusBadge';
import type { DocumentStatus } from '../types';

interface NavbarProps {
  activeFilename?: string;
  status?: DocumentStatus;
}

export const Navbar: React.FC<NavbarProps> = ({ activeFilename, status }) => {
  return (
    <header data-app-header className="w-full shrink-0 border-b border-stone-200 bg-white">
      <div data-testid="navigation-container" className="mx-auto flex min-w-0 w-full flex-wrap items-center justify-between gap-3 px-4 py-3 sm:min-h-16 sm:flex-nowrap sm:px-6 lg:px-8 max-w-[1440px]">
        <BrandIdentity />

        <div className="hidden min-w-0 items-center gap-4 sm:flex">
          {activeFilename ? (
            <div className="flex min-w-0 items-center gap-2 px-3 py-1.5 bg-stone-100 rounded-md border border-stone-200 text-xs text-stone-700">
              <FileText className="w-4 h-4 text-stone-500" />
              <span className="font-medium truncate max-w-[12rem] lg:max-w-xs">{activeFilename}</span>
              {status && <DocumentStatusBadge status={status} />}
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-stone-500 font-medium">

              <span>Upload a research PDF to begin</span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
