import type { SummaryResponse } from '../types/summary';
import { PDF_ID } from './pdfFixtures';

export const SUMMARY: SummaryResponse = {
  document_id: PDF_ID, title: 'Synthetic paper', authors: ['Ada Example'],
  abstract: 'Synthetic abstract.', problem_statement: 'Synthetic problem.',
  methodology: 'Synthetic method.', key_results: 'Synthetic result: 42.',
  conclusion: 'Synthetic conclusion.', generated_at: '2026-11-11T00:00:00Z',
  chunk_set_id: 'a'.repeat(64), summary_profile_id: 'b'.repeat(64),
  llm_model: 'test/model', workflow_version: 'grounded-summary-v1',
  sources: [{ field: 'methodology', chunk_id: 'c'.repeat(64), page_number: 2, quote: 'A synthetic source quote.' }],
  unavailable_fields: [],
};
