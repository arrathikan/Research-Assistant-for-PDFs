import React, { useState, ReactNode } from 'react';
import { Copy, Check, ChevronDown, ChevronUp } from 'lucide-react';

interface SummarySectionProps {
  number: number;
  title: string;
  badge?: string;
  children: ReactNode;
  rawText?: string;
}

export const SummarySection: React.FC<SummarySectionProps> = ({
  number,
  title,
  badge,
  children,
  rawText,
}) => {
  const [copied, setCopied] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  const handleCopy = async () => {
    if (!rawText) return;
    try {
      await navigator.clipboard.writeText(rawText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  return (
    <div
      data-testid={`summary-section-${number}`}
      className="p-5 bg-white rounded-2xl border border-slate-200 shadow-2xs transition-all duration-200"
    >
      <div className="flex items-center justify-between gap-3 mb-3 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-lg bg-brand-50 text-brand-700 flex items-center justify-center text-xs font-bold">
            {number}
          </div>
          <h3 className="text-sm font-bold text-slate-800">{title}</h3>
          {badge && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600 border border-slate-200">
              {badge}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          {rawText && (
            <button
              type="button"
              onClick={handleCopy}
              className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
              title="Copy section text"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          )}

          <button
            type="button"
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
            title={collapsed ? 'Expand section' : 'Collapse section'}
          >
            {collapsed ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {!collapsed && (
        <div className="text-xs text-slate-600 leading-relaxed font-normal">
          {children}
        </div>
      )}
    </div>
  );
};

