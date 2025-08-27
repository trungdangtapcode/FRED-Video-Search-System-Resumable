import React from 'react';
import { UnifiedSearchBox } from '@/components/search/UnifiedSearchBox';
import { useUnifiedSearch } from '@/hooks/useUnifiedSearch';
import type { SearchType } from '@/types';
import { Search } from 'lucide-react';

interface SearchSidebarProps {
  onSearchResults: (results: any[], searchType: SearchType) => void;
  onSearchStart?: () => void;
}

export const SearchSidebar: React.FC<SearchSidebarProps> = ({ onSearchResults, onSearchStart }) => {
  const { searchState, performSearch, clearResults } = useUnifiedSearch();

  const handleSearch = async (query: string, ocr: string, asr: string, topK: number) => {
    console.log('SearchSidebar: Starting unified search with:', { query, ocr, asr, topK });
    onSearchStart?.();
    const results = await performSearch(query, ocr, asr, topK);
    console.log('SearchSidebar: Search completed, got', results.length, 'results');
    // Use 'text' as the search type for compatibility with existing display logic
    onSearchResults(results, 'text');
  };

  const handleClear = () => {
    clearResults();
    onSearchResults([], 'text');
  };

  return (
    <div className="w-64 bg-background border-r border-border h-screen overflow-y-auto">
      <div className="p-2">
        {/* Header */}
        <div className="mb-3">
          <h1 className="text-lg font-bold flex items-center gap-2">
            <Search className="h-4 w-4" />
            L4475
          </h1>
        </div>

        {/* Unified Search Box */}
        <div className="space-y-3">
          <UnifiedSearchBox
            searchState={searchState}
            onSearch={handleSearch}
            onClear={handleClear}
          />
        </div>

        {/* Info Section */}
        <div className="mt-8 p-4 bg-muted/50 rounded-lg">
          <h3 className="text-sm font-medium mb-2">Search Information</h3>
          <div className="text-xs text-muted-foreground space-y-1">
            <p>• <strong>Text Query:</strong> Search by description</p>
            <p>• <strong>OCR:</strong> Search text within images</p>
            <p>• <strong>ASR:</strong> Search speech content</p>
            <p>• At least one field must be filled</p>
            <p>• Results are sorted by similarity</p>
            <p>• Maximum 500 results per search</p>
          </div>
        </div>
      </div>
    </div>
  );
};
