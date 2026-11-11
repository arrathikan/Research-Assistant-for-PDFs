export interface ProcessingStatus {
  document_id: string;
  job_id: string | null;
  status: 'NOT_SCHEDULED' | 'QUEUED' | 'RUNNING' | 'RETRY_WAIT' | 'COMPLETED' | 'DEAD_LETTER';
  stage: 'ingestion' | 'summary' | null;
  step: string | null;
  generation: number;
  attempt: number;
  max_attempts: number;
  retry_at: string | null;
  error_code: string | null;
  requires_review: boolean;
}
