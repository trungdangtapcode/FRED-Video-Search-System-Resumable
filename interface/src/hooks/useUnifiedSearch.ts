import { useState, useCallback } from 'react';
import type { SearchResult } from '@/types';
import { SearchService } from '@/services/searchService';
import { DEFAULT_VALUES } from '@/constants';

export interface UnifiedSearchState {
  query: string;
  ocr: string;
  asr: string;
  topK: number;
  isLoading: boolean;
  results: SearchResult[];
  error: string | null;
}

export const useUnifiedSearch = () => {
  const [searchState, setSearchState] = useState<UnifiedSearchState>({
    query: '',
    ocr: '',
    asr: '',
    topK: DEFAULT_VALUES.TOP_K,
    isLoading: false,
    results: [],
    error: null,
  });

  const updateSearchState = useCallback((updates: Partial<UnifiedSearchState>) => {
    setSearchState(prev => ({ ...prev, ...updates }));
  }, []);

  const performSearch = useCallback(async (
    query: string,
    ocr: string,
    asr: string,
    topK: number
  ): Promise<SearchResult[]> => {
    // Check if at least one field has content
    if (!query.trim() && !ocr.trim() && !asr.trim()) {
      updateSearchState({
        error: 'At least one of query, OCR, or ASR text must be provided',
      });
      return [];
    }

    updateSearchState({
      isLoading: true,
      error: null,
    });

    try {
      const results = await SearchService.unifiedSearch({
        query: query.trim(),
        ocr: ocr.trim(),
        asr: asr.trim(),
        top_k: topK,
      });
      
      updateSearchState({
        isLoading: false,
        results,
        query,
        ocr,
        asr,
        topK,
      });
      
      return results;
    } catch (error) {
      updateSearchState({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Search failed',
      });
      return [];
    }
  }, [updateSearchState]);

  const clearResults = useCallback(() => {
    updateSearchState({
      results: [],
      error: null,
      query: '',
      ocr: '',
      asr: '',
    });
  }, [updateSearchState]);

  return {
    searchState,
    performSearch,
    clearResults,
    updateSearchState,
  };
};
