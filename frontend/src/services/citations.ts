import type { ChatCitation } from '../types/chat';
import type { SummaryResponse, SummarySource } from '../types/summary';

/** Match the existing backend citation identity; canonical source validation still happens there. */
export async function summaryCitation(summary: SummaryResponse, source: SummarySource): Promise<ChatCitation> {
  const value = summary.document_id + ':' + source.chunk_id + ':' + source.page_number + ':' + source.quote;
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  const citationId = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
  return {
    citation_id: citationId, document_id: summary.document_id, chunk_id: source.chunk_id,
    page_number: source.page_number, quote_snippet: source.quote, chunk_set_id: summary.chunk_set_id,
  };
}
