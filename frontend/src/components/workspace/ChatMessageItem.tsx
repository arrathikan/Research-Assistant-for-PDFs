import React from 'react';
import { User, Sparkles } from 'lucide-react';
import { ChatMessage, CitationReference } from '../../types';
import { CitationBadge } from '../common/CitationBadge';

interface ChatMessageItemProps {
  message: ChatMessage;
  onCitationClick?: (citation: CitationReference) => void;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({
  message,
  onCitationClick,
}) => {
  const isUser = message.sender === 'user';

  const formatTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  return (
    <div
      data-testid={`chat-message-${message.sender}`}
      className={`flex gap-3 max-w-2xl ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}
    >
      {/* Avatar */}
      <div
        className={`w-7 h-7 rounded-xl flex items-center justify-center flex-shrink-0 text-xs shadow-2xs ${
          isUser
            ? 'bg-brand-600 text-white'
            : 'bg-emerald-600 text-white'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
      </div>

      {/* Bubble Content */}
      <div
        className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
      >
        <div
          className={`p-3.5 rounded-2xl text-xs leading-relaxed ${
            isUser
              ? 'bg-brand-600 text-white rounded-tr-xs'
              : 'bg-white text-slate-800 border border-slate-200 rounded-tl-xs shadow-2xs'
          }`}
        >
          <div className="whitespace-pre-wrap">{message.content}</div>

          {/* Source Citations */}
          {!isUser && message.citations && message.citations.length > 0 && (
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap items-center gap-1.5">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                Sources:
              </span>
              {message.citations.map((c, i) => (
                <CitationBadge
                  key={`${c.page_number}-${i}`}
                  citation={c}
                  onClick={onCitationClick}
                />
              ))}
            </div>
          )}
        </div>

        <span className="text-[10px] text-slate-400 mt-1 px-1">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
};

