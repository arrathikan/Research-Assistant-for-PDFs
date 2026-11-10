import React from 'react';
import { FileText, ArrowRight, MessageSquare, BookOpen, Clock } from 'lucide-react';
import { DocumentMetadata } from '../../types';

interface DocumentCardProps {
  document: DocumentMetadata;
  onOpen: (doc: DocumentMetadata) => void;
  onViewSummary?: (doc: DocumentMetadata) => void;
  onOpenChat?: (doc: DocumentMetadata) => void;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({
  document,
  onOpen,
  onViewSummary,
  onOpenChat,
}) => {
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatDate = (dateStr: string) => {
    try {
      const dt = new Date(dateStr);
      return dt.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'READY':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'FAILED':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-amber-50 text-amber-700 border-amber-200 animate-pulse';
    }
  };

  return (
    <div
      data-testid="document-card"
      className="p-5 bg-white rounded-2xl border border-slate-200 hover:border-slate-300 hover:shadow-sm transition-all duration-200 flex flex-col justify-between group"
    >
      <div>
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="p-2.5 bg-blue-50 text-blue-600 rounded-xl group-hover:bg-blue-100 transition-colors">
            <FileText className="w-5 h-5" />
          </div>
          <span
            className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold tracking-wider border uppercase ${getStatusBadge(
              document.status
            )}`}
          >
            {document.status}
          </span>
        </div>

        <h3
          className="text-sm font-bold text-slate-800 line-clamp-2 leading-snug group-hover:text-blue-600 transition-colors cursor-pointer"
          onClick={() => onOpen(document)}
          title={document.filename}
        >
          {document.filename}
        </h3>

        <div className="mt-3 flex items-center gap-3 text-[11px] text-slate-400">
          <span>{formatFileSize(document.file_size_bytes)}</span>
          <span>•</span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formatDate(document.created_at)}
          </span>
        </div>
      </div>

      <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-1">
          {onViewSummary && (
            <button
              onClick={() => onViewSummary(document)}
              className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition-colors text-xs font-medium flex items-center gap-1"
              title="View Summary"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span className="text-[11px]">Summary</span>
            </button>
          )}

          {onOpenChat && (
            <button
              onClick={() => onOpenChat(document)}
              className="p-1.5 text-slate-500 hover:text-emerald-600 hover:bg-slate-100 rounded-lg transition-colors text-xs font-medium flex items-center gap-1"
              title="Open Chatbot"
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span className="text-[11px]">Chat</span>
            </button>
          )}
        </div>

        <button
          onClick={() => onOpen(document)}
          className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700 transition-colors"
        >
          <span>Workspace</span>
          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
        </button>
      </div>
    </div>
  );
};
