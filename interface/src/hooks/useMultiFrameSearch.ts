import { useState } from 'react';
import { API_ENDPOINTS } from '@/constants';

interface FrameQuery {
  id: string;
  query: string;
  ocr: string;
  asr: string;
  timestamp: number;
}

interface MultiFrameSearchState {
  frames: FrameQuery[];
  topK: number;
  isLoading: boolean;
  results: any[];
  error: string | null;
}

export const useMultiFrameSearch = () => {
  const [searchState, setSearchState] = useState<MultiFrameSearchState>({
    frames: [{
      id: 'frame_1',
      query: '',
      ocr: '',
      asr: '',
      timestamp: 0
    }],
    topK: 100,
    isLoading: false,
    results: [],
    error: null,
  });

  const performSearch = async (frames: FrameQuery[], topK: number): Promise<any[]> => {
    console.log('Performing multi-frame search with:', { frames, topK });
    
    setSearchState(prev => ({
      ...prev,
      isLoading: true,
      error: null,
      frames,
      topK,
    }));

    try {
      // Filter out empty frames and prepare request data
      const validFrames = frames
        .filter(frame => frame.query.trim() || frame.ocr.trim() || frame.asr.trim())
        .map(frame => ({
          query: frame.query.trim() || undefined,
          ocr: frame.ocr.trim() || undefined,
          asr: frame.asr.trim() || undefined,
          timestamp: frame.timestamp || 0,
        }));

      if (validFrames.length === 0) {
        throw new Error('At least one frame must have content');
      }

      const requestBody = {
        frames: validFrames,
        top_k: topK,
      };

      console.log('Sending multi-frame search request:', requestBody);

      const response = await fetch(API_ENDPOINTS.SEARCH.replace('/retrieve', '/retrieve_multi_frame'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      const results = await response.json();
      console.log('Multi-frame search completed, got', results.length, 'results');

      setSearchState(prev => ({
        ...prev,
        isLoading: false,
        results,
      }));

      return results;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Search failed';
      console.error('Multi-frame search error:', errorMessage);
      
      setSearchState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
        results: [],
      }));
      
      throw error;
    }
  };

  const clearResults = () => {
    setSearchState(prev => ({
      ...prev,
      results: [],
      error: null,
      frames: [{
        id: 'frame_1',
        query: '',
        ocr: '',
        asr: '',
        timestamp: 0
      }],
    }));
  };

  return {
    searchState,
    performSearch,
    clearResults,
  };
};
