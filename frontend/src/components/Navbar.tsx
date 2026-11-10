import React from 'react';
import { BookOpen, FileText, Sparkles } from 'lucide-react';

interface NavbarProps {
  activeFilename?: string;
  status?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ activeFilename, status }) => {
  return (
    <header className="h-16 border-b border-slate-200 bg-white px-6 flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-600 rounded-lg text-white">
          <BookOpen className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-900 leading-tight">ResearchAI</h1>
          <p className="text-xs text-slate-500">AI Academic Paper Assistant</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {activeFilename ? (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-md border border-slate-200 text-xs text-slate-700">
            <FileText className="w-4 h-4 text-slate-500" />
            <span className="font-medium truncate max-w-xs">{activeFilename}</span>
            {status && (
              <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-100 text-blue-700">
                {status}
              </span>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
            <Sparkles className="w-4 h-4 text-amber-500" />
            <span>Upload a research PDF to begin</span>
          </div>
        )}
      </div>
    </header>
  );
};
