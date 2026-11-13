import React from 'react';
import { Bookmark } from 'lucide-react';
import { CitationReference } from '../../types';

interface CitationBadgeProps {
  citation: CitationReference;
  onClick?: (citation: CitationReference) => void;
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({ citation, onClick }) => {
  return (
    <button
      type="button"
      onClick={() => onClick?.(citation)}
      className="inline-flex items-center gap-1 px-2 py-0.5 bg-brand-50 hover:bg-brand-100 text-brand-700 border border-brand-200 rounded-md text-[11px] font-medium transition-colors cursor-pointer group shadow-2xs"
      title={`Jump to Page ${citation.page_number}: "${citation.quote_snippet}"`}
    >
      <Bookmark className="w-3 h-3 text-brand-500 group-hover:text-brand-700" />
      <span>Page {citation.page_number}</span>
    </button>
  );
};
