import { useState, useCallback } from 'react';
import type { SearchState, SearchType, SearchResult } from '@/types';
import { SearchService } from '@/services/searchService';
import { DEFAULT_VALUES } from '@/constants';

export const useSearch = () => {
  const [searchStates, setSearchStates] = useState<Record<SearchType, SearchState>>({
    text: {
      query: '',
      topK: DEFAULT_VALUES.TOP_K,
      isLoading: false,
      results: [],
      error: null,
    },
    ocr: {
      query: '',
      topK: DEFAULT_VALUES.TOP_K,
      isLoading: false,
      results: [],
      error: null,
    },
    asr: {
      query: '',
      topK: DEFAULT_VALUES.TOP_K,
      isLoading: false,
      results: [],
      error: null,
    },
  });

  const updateSearchState = useCallback((
    searchType: SearchType,
    updates: Partial<SearchState>
  ) => {
    setSearchStates(prev => ({
      ...prev,
      [searchType]: { ...prev[searchType], ...updates },
    }));
  }, []);

  const performSearch = useCallback(async (
    searchType: SearchType,
    query: string,
    topK: number
  ): Promise<SearchResult[]> => {
    if (searchType !== 'text') {
      updateSearchState(searchType, {
        error: `${searchType.toUpperCase()} search is not available yet`,
      });
      return [];
    }

    updateSearchState(searchType, {
      isLoading: true,
      error: null,
    });

    try {
      const results = await SearchService.searchByText({ query, top_k: topK });
      updateSearchState(searchType, {
        isLoading: false,
        results,
        query,
        topK,
      });
      return results;
    } catch (error) {
      updateSearchState(searchType, {
        isLoading: false,
        error: error instanceof Error ? error.message : 'Search failed',
      });
      return [];
    }
  }, [updateSearchState]);

  const clearResults = useCallback((searchType: SearchType) => {
    updateSearchState(searchType, {
      results: [],
      error: null,
      query: '',
    });
  }, [updateSearchState]);

  return {
    searchStates,
    performSearch,
    clearResults,
    updateSearchState,
  };
};
