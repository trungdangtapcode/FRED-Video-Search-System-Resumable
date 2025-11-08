import { useState } from 'react';
import type { SearchResult } from '@/types';
import { API_ENDPOINTS } from '@/constants';

interface ImageSearchState {
  isLoading: boolean;
  error: string | null;
  results: SearchResult[];
}

export const useImageSearch = () => {
  const [searchState, setSearchState] = useState<ImageSearchState>({
    isLoading: false,
    error: null,
    results: []
  });

  const performSearch = async (imageFile: File, topK: number = 5): Promise<SearchResult[]> => {
    setSearchState(prev => ({
      ...prev,
      isLoading: true,
      error: null
    }));

    try {
      const formData = new FormData();
      formData.append('image', imageFile);
      formData.append('top_k', topK.toString());

      const response = await fetch(`${API_ENDPOINTS.SEARCH}_image`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const results: SearchResult[] = await response.json();
      
      setSearchState({
        isLoading: false,
        error: null,
        results
      });

      return results;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setSearchState({
        isLoading: false,
        error: errorMessage,
        results: []
      });
      
      throw error;
    }
  };

  const clearResults = () => {
    setSearchState({
      isLoading: false,
      error: null,
      results: []
    });
  };

  return {
    searchState,
    performSearch,
    clearResults
  };
};
