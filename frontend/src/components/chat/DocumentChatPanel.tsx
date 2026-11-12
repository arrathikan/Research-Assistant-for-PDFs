import { Loader2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { api, ApiError } from '../../services/api';
import type { ChatCitation, ChatTurn } from '../../types/chat';
import { CitedAnswer } from './CitedAnswer';

interface Props { documentId?: string; onCitationClick?: (citation: ChatCitation) => void; }

export function DocumentChatPanel({ documentId, onCitationClick }: Props) {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState('');
  const [pending, setPending] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [reset, setReset] = useState(0);
  const epoch = useRef(0);
  const conversation = useRef<string | undefined>();
  const valid = !!documentId && /^[0-9a-f]{24}$/i.test(documentId);
  const key = `researchai.chat.${documentId}`;

  useEffect(() => {
    const generation = ++epoch.current;
    conversation.current = undefined;
    setTurns([]); setPending(''); setInput(''); setError(''); setLoading(false);
    if (!valid || !documentId) return;
    let saved: string | null = null;
    try { saved = sessionStorage.getItem(key); } catch { /* Chat also works without browser storage. */ }
    if (!saved || !/^[0-9a-f]{32}$/.test(saved)) return;
    const id = documentId.toLowerCase();
    conversation.current = saved;
    setLoading(true);
    void api.getChatHistory(id, saved).then(history => {
      if (generation !== epoch.current) return;
      if (history.document_id !== id || history.conversation_id !== saved || history.turns.some(turn => turn.response.document_id !== id)) {
        throw new Error('History mismatch');
      }
      setTurns(history.turns);
    }).catch(() => {
      if (generation === epoch.current) setError('Saved conversation is unavailable. Start a new conversation to continue.');
    }).finally(() => { if (generation === epoch.current) setLoading(false); });
    return () => { epoch.current++; };
  }, [documentId, valid, key, reset]);

  const startNew = () => {
    try { sessionStorage.removeItem(key); } catch { /* Optional storage. */ }
    setReset(value => value + 1);
  };

  async function send(event: React.FormEvent) {
    event.preventDefault();
    if (!documentId || !valid || !input.trim() || loading) return;
    const question = input.trim();
    const generation = epoch.current;
    const id = documentId.toLowerCase();
    setPending(question); setInput(''); setLoading(true); setError('');
    try {
      const response = await api.sendChatQuery(id, question, conversation.current);
      if (generation !== epoch.current) return;
      if (response.document_id !== id || !response.answer.trim() || response.citations.some(source => source.document_id !== id)) throw new Error('Response mismatch');
      conversation.current = response.conversation_id;
      try { sessionStorage.setItem(key, response.conversation_id); } catch { /* Optional storage. */ }
      setTurns(previous => [...previous, { question, response, created_at: new Date().toISOString() }]);
    } catch (failure: unknown) {
      if (generation !== epoch.current) return;
      setInput(question);
      setError(failure instanceof ApiError && failure.status === 409
        ? 'The document is still processing, or this conversation changed. Try later or start a new conversation.'
        : 'Chat is unavailable right now. Please try again later.');
    } finally {
      if (generation === epoch.current) { setPending(''); setLoading(false); }
    }
  }

  return (
    <section className="min-w-0 w-full space-y-4 [overflow-wrap:anywhere]" aria-label="Document chatbot">
      <div className="flex justify-between items-center">
        <h2 className="font-semibold text-slate-800">Chat with your paper</h2>
        <button type="button" onClick={startNew} disabled={loading} className="min-h-10 rounded-lg px-2 text-xs font-medium text-slate-600 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 disabled:opacity-50">New conversation</button>
      </div>
      {!valid && <p role="status">Upload a PDF to ask questions about it.</p>}
      {valid && turns.length === 0 && !loading && <p className="text-sm text-slate-600">Ask about the methods, findings or limitations—or request an overview.</p>}
      <div className="space-y-4" aria-label="Chat messages">
        {turns.map(turn => (
          <article key={turn.response.turn_id} className="space-y-4">
            <p className="ml-auto max-w-[90%] rounded-2xl rounded-tr-sm bg-blue-50 px-4 py-3 text-sm leading-6 text-slate-800 whitespace-pre-wrap">{turn.question}</p>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
              <p className="mb-3 text-xs font-semibold text-blue-700">ResearchAI</p>
              <CitedAnswer answer={turn.response.answer} citations={turn.response.citations} onCitationClick={onCitationClick} />
              {turn.response.citations.length > 0 && <details className="mt-4 border-t border-slate-100 pt-3">
                <summary className="w-fit cursor-pointer rounded text-xs font-medium text-slate-500 hover:text-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600">Sources ({turn.response.citations.length})</summary>
                <ol aria-label="Supporting sources" className="mt-3 space-y-3 text-xs text-slate-600">
                  {turn.response.citations.map(source => <li key={source.citation_id} className="rounded-lg bg-slate-50 p-3">
                    {onCitationClick ? <button type="button" className="rounded px-1 py-1 font-semibold text-blue-700 hover:bg-blue-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600" onClick={() => onCitationClick(source)}>Page {source.page_number}</button>
                      : <span className="font-semibold">Page {source.page_number}</span>}
                    <blockquote className="mt-1 leading-6">{source.quote_snippet}</blockquote>
                  </li>)}
                </ol>
              </details>}
            </div>
          </article>
        ))}
        {pending && <p className="ml-auto max-w-[90%] rounded-2xl bg-blue-50 p-3 text-sm">{pending}</p>}
      </div>
      {loading && <p role="status" className="flex items-center gap-2 text-xs text-slate-500"><Loader2 size={14} aria-hidden="true" className="motion-safe:animate-spin" />{pending ? 'Preparing your answer…' : 'Loading conversation…'}</p>}
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <form onSubmit={send} className="flex gap-2">
        <input aria-label="Question" placeholder="Ask a question about this research paper..." value={input} onChange={event => setInput(event.target.value)} maxLength={2000} disabled={!valid || loading} className="min-w-0 flex-1 rounded-lg border border-slate-300 p-3 text-sm" />
        <button type="submit" aria-label="Send Message" disabled={!valid || loading || !input.trim()} className="rounded-lg bg-blue-600 text-white p-3 text-sm disabled:opacity-50">Send</button>
      </form>
    </section>
  );
}
