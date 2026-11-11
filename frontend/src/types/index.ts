/**
 * Shared TypeScript type definitions for ResearchAI frontend.
 * Strictly aligned with backend Pydantic models.
 */

export type DocumentStatus =
  | 'PENDING'
  | 'PARSING'
  | 'EMBEDDING'
  | 'SUMMARIZING'
  | 'READY'
  | 'FAILED';

export type ChunkingStatus = 'NOT_STARTED' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export type ParsingStatus = 'NOT_STARTED' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export interface DocumentMetadata {
  id?: string;
  sha256: string;
  filename: string;
  file_size_bytes: number;
  gridfs_file_id?: string;
  page_count?: number;
  status: DocumentStatus;
  parsing_status?: ParsingStatus;
  parsed_at?: string | null;
  chunking_status?: ChunkingStatus;
  chunked_at?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface StructuredSummary {
  document_id: string;
  title: string;
  authors: string[];
  abstract: string;
  problem_statement: string;
  methodology: string;
  key_results: string;
  conclusion: string;
  generated_at: string;
}

export interface CitationReference {
  page_number: number;
  quote_snippet: string;
  chunk_id?: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  citations?: CitationReference[];
  timestamp: string;
}

export interface UploadResponse {
  document: DocumentMetadata;
  message: string;
  is_duplicate: boolean;
}

export type NavigationTab = 'dashboard' | 'upload' | 'workspace';

export type WorkspaceTab = 'summary' | 'chat' | 'pdf';
