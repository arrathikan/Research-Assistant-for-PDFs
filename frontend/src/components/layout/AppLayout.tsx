import React, { ReactNode } from 'react';
import { Navbar } from './Navbar';
import { NavigationTab, DocumentMetadata } from '../../types';

interface AppLayoutProps {
  children: ReactNode;
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  activeDoc: DocumentMetadata | null;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  activeTab,
  onSelectTab,
  activeDoc,
}) => {
  return (
    <div className="h-dvh w-full min-w-0 flex flex-col bg-slate-50 text-slate-900 overflow-hidden">
      <Navbar
        activeTab={activeTab}
        onSelectTab={onSelectTab}
        activeDoc={activeDoc}
      />
      <main id="main-content" tabIndex={-1} className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        {children}
      </main>
    </div>
  );
};
