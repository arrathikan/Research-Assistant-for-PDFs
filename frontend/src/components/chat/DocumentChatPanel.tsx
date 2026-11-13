import { ArrowUpRight, BookOpen, Loader2, MessageSquare, Plus, Send } from 'lucide-react';
import { useEffect, useId, useRef, useState } from 'react';
import { api, ApiError } from '../../services/api';
import type { ChatCitation, ChatTurn } from '../../types/chat';
import { CitedAnswer } from './CitedAnswer';

interface Props { documentId?: string; onCitationClick?: (citation: ChatCitation) => void; }

export function DocumentChatPanel({ documentId, onCitationClick }: Props) {
  const inputId = useId();
  const hintId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
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

  async function sendQuestion(value: string) {
    if (!documentId || !valid || !value.trim() || loading) return;
    const question = value.trim();
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

  const suggestions = [
    'What methodology was used?', 'What are the main findings?', 'Who wrote this paper?',
    'When was it published?', 'Summarize the research.', 'What is the main contribution?', 'What are the limitations?',
    'What does the research say about a specific topic?',
  ];
  const suggestionButton = (question: string) => <button type="button" key={question}
    onClick={() => { setInput(question); inputRef.current?.focus(); }}
    className="flex min-h-12 items-center justify-between gap-3 rounded-xl border border-stone-200 px-4 py-3 text-left text-sm text-stone-700 hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700">
    {question}<ArrowUpRight size={15} aria-hidden="true" className="shrink-0 text-stone-500" />
  </button>;

  return (
    <section className="min-w-0 w-full space-y-5 [overflow-wrap:anywhere]" aria-label="Document chatbot">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><p className="ui-eyebrow mb-1">Paper assistant</p><h2 className="text-xl font-semibold tracking-tight text-stone-900">Chat with your paper</h2></div>
        <button type="button" onClick={startNew} disabled={loading} className="ui-button ui-button-secondary"><Plus size={16} aria-hidden="true" />New conversation</button>
      </div>
      {!valid && <p role="status" className="ui-card p-5 text-sm text-stone-600">Choose an uploaded paper from your library to start a conversation.</p>}
      {valid && turns.length === 0 && !loading && !error && <div className="rounded-xl border border-stone-200 bg-white p-5 sm:p-7">
        <span className="mb-4 hidden h-12 w-12 sm:inline-flex items-center justify-center rounded-2xl bg-brand-50 text-brand-700"><MessageSquare size={23} aria-hidden="true" /></span>
        <h3 className="text-lg font-semibold text-stone-900">Explore your paper</h3>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-600">Explore the authors, methods and findings. Start with a question below or ask your own.</p>
        <div className="mt-4 grid gap-2 sm:grid-cols-2" aria-label="Suggested questions">
          {suggestions.slice(0, 2).map(suggestionButton)}
        </div>
        <details className="mt-3">
          <summary className="min-h-8 w-fit cursor-pointer rounded py-1 text-xs font-semibold text-stone-600 hover:text-brand-700">More question ideas</summary>
          <div className="mt-2 grid gap-2 sm:grid-cols-2">{suggestions.slice(2).map(suggestionButton)}</div>
        </details>
      </div>}
      <div className="space-y-6" role="log" aria-label="Chat messages" aria-live="polite" aria-relevant="additions" aria-busy={loading}>
        {turns.map(turn => (
          <article key={turn.response.turn_id} className="space-y-4">
            <p className="ml-auto w-fit max-w-[85%] sm:max-w-[70ch] rounded-xl rounded-tr-sm border border-stone-200 bg-white px-4 py-3 text-sm leading-7 text-stone-800 whitespace-pre-wrap">{turn.question}</p>
            <div className="w-full max-w-[90ch] border-l-2 border-stone-200 py-2 pl-4 sm:pl-5">
              <p className="mb-4 flex items-center gap-2 text-xs font-semibold text-brand-700"><BookOpen size={16} aria-hidden="true" />ResearchAI</p>
              <CitedAnswer answer={turn.response.answer} citations={turn.response.citations} onCitationClick={onCitationClick} />
              {turn.response.citations.length > 0 && <details className="mt-5 border-t border-stone-100 pt-3">
                <summary className="min-h-8 w-fit cursor-pointer rounded py-1 text-xs font-semibold text-stone-600 hover:text-brand-700">Sources ({turn.response.citations.length})</summary>
                <ol aria-label="Supporting sources" className="mt-3 space-y-3 text-sm text-stone-600">
                  {turn.response.citations.map(source => <li key={source.citation_id} className="border-l-2 border-stone-200 pl-3">
                    {onCitationClick ? <button type="button" className="min-h-8 rounded-lg px-2 py-1 text-xs font-semibold text-brand-700 hover:bg-brand-100" onClick={() => onCitationClick(source)}>Page {source.page_number}</button>
                      : <span className="font-semibold">Page {source.page_number}</span>}
                    <blockquote className="mt-1 leading-7">{source.quote_snippet}</blockquote>
                  </li>)}
                </ol>
              </details>}
            </div>
          </article>
        ))}
        {pending && <p className="ml-auto w-fit max-w-[85%] sm:max-w-[70ch] rounded-xl border border-stone-200 bg-white p-4 text-sm leading-7">{pending}</p>}
      </div>
      {loading && <div className="ui-card max-w-[90ch] p-5">
        <p role="status" className="flex items-center gap-2 text-sm text-stone-600"><Loader2 size={16} aria-hidden="true" className="motion-safe:animate-spin" />{pending ? 'Preparing your answer…' : 'Loading conversation…'}</p>
        <div aria-hidden="true" className="mt-4 space-y-2"><div className="ui-skeleton h-3 w-4/5" /><div className="ui-skeleton h-3 w-3/5" /></div>
      </div>}
      {error && <div className="rounded-xl border border-red-200 bg-white p-4">
        <p role="alert" className="text-sm leading-6 text-red-700">{error}</p>
        {input.trim() && <button type="button" disabled={loading} className="ui-button ui-button-secondary mt-3" onClick={() => void sendQuestion(input)}>Retry question</button>}
      </div>}
      <form onSubmit={event => { event.preventDefault(); void sendQuestion(input); }} className={(turns.length > 0 || pending ? 'sticky bottom-0 ' : '') + 'rounded-xl border border-stone-200 bg-white p-3 shadow-sm sm:p-4'}>
        <label htmlFor={inputId} className="mb-2 block text-xs font-semibold text-stone-700">Question</label>
        <div className="flex gap-2">
          <input id={inputId} ref={inputRef} aria-describedby={hintId} placeholder="Ask a question about this research paper..." value={input} onChange={event => setInput(event.target.value)}
            onKeyDown={event => { if (event.key === 'Enter' && event.nativeEvent.isComposing) event.preventDefault(); }}
            maxLength={2000} disabled={!valid || loading} className="ui-field min-w-0 flex-1" />
          <button type="submit" aria-label="Send Message" disabled={!valid || loading || !input.trim()} className="ui-button ui-button-primary px-3 sm:px-4"><Send size={18} aria-hidden="true" /><span className="hidden sm:inline">Send</span></button>
        </div>
        <p id={hintId} className="mt-2 text-xs leading-5 text-stone-500">AI can miss details. Check the linked sources for important claims.</p>
      </form>
    </section>
  );
}
