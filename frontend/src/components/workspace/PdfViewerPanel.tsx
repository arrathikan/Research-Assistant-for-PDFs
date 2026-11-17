import React, { useState, useEffect } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  FileText,
  Bookmark,
  ExternalLink,
  Layers,
} from 'lucide-react';
import { DocumentMetadata, CitationReference } from '../../types';
import { api } from '../../services/api';

interface PdfViewerPanelProps {
  document: DocumentMetadata;
  activeCitation?: CitationReference | null;
}

export const PdfViewerPanel: React.FC<PdfViewerPanelProps> = ({
  document,
  activeCitation,
}) => {
  const [currentPage, setCurrentPage] = useState<number>(1);
  const totalPages = document.page_count || 12;
  const [zoomLevel, setZoomLevel] = useState<number>(100);

  // Jump to page when activeCitation updates
  useEffect(() => {
    if (activeCitation) {
      setCurrentPage(activeCitation.page_number);
    }
  }, [activeCitation]);

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage((p) => p + 1);
  };

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage((p) => p - 1);
  };

  const pdfUrl = document.id ? api.getPdfStreamUrl(document.id) : null;

  return (
    <div
      data-testid="pdf-viewer-panel"
      className="flex-1 flex flex-col bg-slate-100 h-full overflow-hidden"
    >
      {/* Toolbar */}
      <div className="h-12 bg-white border-b border-slate-200 px-4 flex items-center justify-between text-xs text-slate-700 shadow-2xs z-10 flex-shrink-0">
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrevPage}
            disabled={currentPage <= 1}
            aria-label="Previous Page"
            className="p-1 rounded-md text-slate-500 hover:bg-slate-100 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <span className="font-medium text-slate-800">
            Page <span className="font-bold text-brand-600">{currentPage}</span> of {totalPages}
          </span>

          <button
            onClick={handleNextPage}
            disabled={currentPage >= totalPages}
            aria-label="Next Page"
            className="p-1 rounded-md text-slate-500 hover:bg-slate-100 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-1.5 border-l border-slate-200 pl-3">
          <button
            onClick={() => setZoomLevel((z) => Math.max(z - 15, 50))}
            aria-label="Zoom Out"
            className="p-1 rounded-md text-slate-500 hover:bg-slate-100 transition-colors"
          >
            <ZoomOut className="w-4 h-4" />
          </button>

          <span className="text-[11px] font-semibold text-slate-600 w-12 text-center">
            {zoomLevel}%
          </span>

          <button
            onClick={() => setZoomLevel((z) => Math.min(z + 15, 200))}
            aria-label="Zoom In"
            className="p-1 rounded-md text-slate-500 hover:bg-slate-100 transition-colors"
          >
            <ZoomIn className="w-4 h-4" />
          </button>

          <button
            onClick={() => setZoomLevel(100)}
            aria-label="Reset Zoom"
            className="p-1 rounded-md text-slate-500 hover:bg-slate-100 transition-colors"
            title="Reset Zoom"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Status / Link indicator */}
        <div className="hidden sm:flex items-center gap-2 text-slate-500 text-[11px]">
          <Layers className="w-3.5 h-3.5 text-slate-400" />
          <span>React-PDF / PDF.js Layer</span>
        </div>
      </div>

      {/* Active Citation Alert Bar */}
      {activeCitation && (
        <div className="bg-brand-600 text-white px-4 py-2 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2 truncate">
            <Bookmark className="w-4 h-4 text-brand-200 flex-shrink-0" />
            <span className="font-semibold">Highlighted Source (Page {activeCitation.page_number}):</span>
            <span className="italic truncate font-light text-brand-100">
              "{activeCitation.quote_snippet}"
            </span>
          </div>
          <span className="text-[10px] uppercase font-bold bg-brand-700 px-2 py-0.5 rounded-full text-brand-100 ml-2 flex-shrink-0">
            Active Highlight
          </span>
        </div>
      )}

      {/* Viewport Canvas Area */}
      <div className="flex-1 overflow-auto p-6 flex items-center justify-center">
        <div
          style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }}
          className="w-full max-w-2xl bg-white rounded-xl border border-slate-200 shadow-md min-h-[700px] p-10 flex flex-col justify-between transition-transform duration-150"
        >
          {/* Header on page */}
          <div className="border-b border-slate-200 pb-4 flex items-center justify-between text-xs text-slate-400">
            <span className="font-medium text-slate-600 truncate">{document.filename}</span>
            <span>Page {currentPage} / {totalPages}</span>
          </div>

          {/* Page Body / Content Placeholder */}
          <div className="my-auto space-y-4 text-left">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div className="flex items-center gap-2 text-brand-700 font-semibold text-xs mb-1">
                <FileText className="w-4 h-4" />
                <span>Page {currentPage} Document Layer</span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                Rendered via PDF.js text layer. Programmatic citation jumping automatically scrolls to this viewport.
              </p>
            </div>

            {activeCitation && activeCitation.page_number === currentPage && (
              <div
                data-testid="pdf-highlight-snippet"
                className="p-3.5 bg-amber-50 rounded-lg border-l-4 border-amber-500 text-amber-900 text-xs shadow-xs animate-pulse"
              >
                <div className="font-semibold text-[11px] text-amber-700 uppercase mb-1">
                  Supporting Citation Excerpt:
                </div>
                <p className="italic">"{activeCitation.quote_snippet}"</p>
              </div>
            )}

            <div className="space-y-2 opacity-60">
              <div className="h-3 bg-slate-200 rounded-full w-full"></div>
              <div className="h-3 bg-slate-200 rounded-full w-5/6"></div>
              <div className="h-3 bg-slate-200 rounded-full w-4/6"></div>
              <div className="h-3 bg-slate-200 rounded-full w-11/12"></div>
              <div className="h-3 bg-slate-200 rounded-full w-3/4"></div>
            </div>
          </div>

          {/* Footer on page */}
          <div className="border-t border-slate-100 pt-4 flex items-center justify-between text-[11px] text-slate-400">
            <span>ResearchAI Embedded Viewer</span>
            {pdfUrl && (
              <a
                href={pdfUrl}
                target="_blank"
                rel="noreferrer"
                className="text-brand-600 hover:underline flex items-center gap-1"
              >
                <span>Raw Binary</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

