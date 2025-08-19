// Search related types
export interface SearchRequest {
  query: string;
  top_k: number;
}

export interface SearchResult {
  fps: number;
  frame_idx: number;
  frame_path: string;
  timestamp: number;
  video_path: string;
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
