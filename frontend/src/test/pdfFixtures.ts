import type { DocumentMetadata } from '../types';
import type { ChatCitation } from '../types/chat';
export const PDF_ID = '507f1f77bcf86cd799439011';
export const PDF_DOCUMENT: DocumentMetadata = { id: PDF_ID, sha256: 'a'.repeat(64), filename: 'synthetic.pdf', file_size_bytes: 400,
  status: 'READY', page_count: 3, created_at: '2026-11-11T00:00:00Z', updated_at: '2026-11-11T00:00:00Z' };
export const PDF_CITATION: ChatCitation = { document_id: PDF_ID, citation_id: 'b'.repeat(64), chunk_id: 'c'.repeat(64),
  chunk_set_id: 'd'.repeat(64), parse_run_id: 'e'.repeat(32), page_number: 2, quote_snippet: 'Synthetic evidence.',
  page_width: 600, page_height: 800, bounding_boxes: [{ element_id: 'line-1', x: 60, y: 80, width: 180, height: 20,
    coordinate_system: 'points', origin: 'top_left', rotation_degrees: 0, renderable: true }] };
