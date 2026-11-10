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
    <div className="h-screen w-screen flex flex-col bg-slate-50 text-slate-900 overflow-hidden">
      <Navbar
        activeTab={activeTab}
        onSelectTab={onSelectTab}
        activeDoc={activeDoc}
      />
      <main className="flex-1 flex flex-col overflow-hidden">
        {children}
      </main>
    </div>
  );
};
