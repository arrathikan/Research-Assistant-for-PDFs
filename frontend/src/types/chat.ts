import type { CitationReference } from './index';
export interface ChatCitation extends CitationReference {
  citation_id: string;
  document_id: string;
  chunk_id: string;
}
export interface ChatResponse {
  document_id: string;
  conversation_id: string;
  turn_id: string;
  answer: string;
  citations: ChatCitation[];
  is_out_of_scope: boolean;
}
export interface ChatTurn {
  question: string;
  response: ChatResponse;
  created_at: string;
}
export interface ChatHistory {
  document_id: string;
  conversation_id: string;
  turns: ChatTurn[];
}
