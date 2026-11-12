import type { DocumentMetadata, UploadResponse } from '../types';
import type { ProcessingStatus } from '../types/processing';
import type { SummaryResponse } from '../types/summary';

export const ID = '507f1f77bcf86cd799439011';
export const OTHER_ID = '507f1f77bcf86cd799439012';
export const PAPER: DocumentMetadata = {
  id: ID, sha256: 'a'.repeat(64), filename: 'paper.pdf', file_size_bytes: 1048576,
  status: 'PENDING', embedding_status: 'NOT_STARTED', page_count: 3,
  created_at: '2026-11-12T00:00:00Z', updated_at: '2026-11-12T00:00:00Z',
};
export const READY: DocumentMetadata = { ...PAPER, status: 'READY', embedding_status: 'COMPLETED' };
export const STORED: UploadResponse = { document: PAPER, message: 'Raw internal server message', is_duplicate: false };
export const QUEUED: ProcessingStatus = {
  document_id: ID, job_id: 'b'.repeat(64), status: 'QUEUED', stage: 'ingestion',
  step: null, generation: 1, attempt: 1, max_attempts: 3,
  retry_at: null, error_code: null, requires_review: false,
};
export const SUMMARY: SummaryResponse = {
  document_id: ID, title: 'Synthetic research paper', authors: ['Example Researcher'],
  abstract: 'Synthetic abstract.', problem_statement: 'Synthetic problem.',
  methodology: 'Synthetic method.', key_results: 'Synthetic result.',
  conclusion: 'Synthetic conclusion.', generated_at: '2026-11-12T00:00:00Z',
  chunk_set_id: 'c'.repeat(64), summary_profile_id: 'd'.repeat(64),
  llm_model: 'test/model', workflow_version: 'test-workflow', sources: [], unavailable_fields: [],
};
