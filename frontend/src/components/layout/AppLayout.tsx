import React, { ReactNode, useEffect } from 'react';
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
  useEffect(() => {
    const page = activeTab === 'dashboard' ? 'Paper Library' : activeTab === 'upload' ? 'Upload Paper' : 'Workspace';
    document.title = `${page} | ResearchAI`;
  }, [activeTab]);
  return (
    <div className="app-shell h-dvh w-full min-w-0 bg-stone-50 text-stone-900 overflow-hidden">
      <Navbar
        activeTab={activeTab}
        onSelectTab={onSelectTab}
        activeDoc={activeDoc}
      />
      <main id="main-content" tabIndex={-1} className="app-main flex min-h-0 min-w-0 flex-col overflow-hidden">
        {children}
      </main>
    </div>
  );
};
