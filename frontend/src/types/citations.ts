export interface CitationBox {
  element_id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  coordinate_system: 'normalized' | 'points' | 'provider';
  origin: 'top_left' | 'unknown';
  rotation_degrees: number | null;
  renderable: boolean;
}

export interface SourceAnchorFields {
  chunk_set_id?: string | null;
  parse_run_id?: string | null;
  page_width?: number | null;
  page_height?: number | null;
  source_element_ids?: string[];
  bounding_boxes?: CitationBox[];
}
