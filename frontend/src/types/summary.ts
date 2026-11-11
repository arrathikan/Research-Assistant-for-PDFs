import type { StructuredSummary } from './index';

export type SummaryField =
  | 'title' | 'authors' | 'abstract' | 'problem_statement'
  | 'methodology' | 'key_results' | 'conclusion';

export interface SummarySource {
  field: SummaryField;
  chunk_id: string;
  page_number: number;
  quote: string;
}

export interface SummaryResponse extends StructuredSummary {
  chunk_set_id: string;
  summary_profile_id: string;
  llm_model: string;
  workflow_version: string;
  sources: SummarySource[];
  unavailable_fields: SummaryField[];
}
