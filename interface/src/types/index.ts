// Search related types
export interface SearchRequest {
  query?: string;
  ocr?: string;
  asr?: string;
  top_k: number;
}

export interface UnifiedSearchRequest {
  query: string;
  ocr: string;
  asr: string;
  top_k: number;
}

export interface SearchResult {
  fps: number;
  frame_idx: number;
  frame_path: string;
  timestamp: number;
  video_path: string;
  compressed_frame_path: string;
  metadata_index?: number; // Index in the metadata list for DINOv3 similarity search
}

export type SearchResponse = SearchResult[];

// Search types
export type SearchType = 'text' | 'ocr' | 'asr';

export interface SearchState {
  query: string;
  topK: number;
  isLoading: boolean;
  results: SearchResult[];
  error: string | null;
}

// Display modes
export type DisplayMode = 'all' | 'grouped';

export interface GroupedResults {
  videoPath: string;
  videoName: string;
  frames: SearchResult[];
}
