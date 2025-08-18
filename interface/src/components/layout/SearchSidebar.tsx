import React from 'react';
import { SearchBox } from '@/components/search/SearchBox';
import { useSearch } from '@/hooks/useSearch';
import type { SearchType } from '@/types';
import { SEARCH_TYPES } from '@/constants';
import { Search } from 'lucide-react';

interface SearchSidebarProps {
  onSearchResults: (results: any[], searchType: SearchType) => void;
  onSearchStart?: () => void;
}

export const SearchSidebar: React.FC<SearchSidebarProps> = ({ onSearchResults, onSearchStart }) => {
  const { searchStates, performSearch, clearResults } = useSearch();

  const handleSearch = async (searchType: SearchType, query: string, topK: number) => {
    console.log('SearchSidebar: Starting search for', searchType, 'with query:', query);
    onSearchStart?.();
    const results = await performSearch(searchType, query, topK);
    console.log('SearchSidebar: Search completed, got', results.length, 'results');
    onSearchResults(results, searchType);
  };

  const handleClear = (searchType: SearchType) => {
    clearResults(searchType);
    onSearchResults([], searchType);
  };

  return (
    <div className="w-72 bg-background border-r border-border h-screen overflow-y-auto">
      <div className="p-4">
        {/* Header */}
        <div className="mb-4">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Search className="h-5 w-5" />
            Video Search
          </h1>
        </div>

        {/* Search Boxes */}
        <div className="space-y-4">
          {Object.values(SEARCH_TYPES).map((config) => {
            const searchType = config.key;
            return (
              <SearchBox
                key={searchType}
                searchType={searchType}
                searchState={searchStates[searchType]}
                onSearch={(query, topK) => handleSearch(searchType, query, topK)}
                onClear={() => handleClear(searchType)}
              />
            );
          })}
        </div>

        {/* Info Section */}
        <div className="mt-8 p-4 bg-muted/50 rounded-lg">
          <h3 className="text-sm font-medium mb-2">Search Information</h3>
          <div className="text-xs text-muted-foreground space-y-1">
            <p>• <strong>Text Search:</strong> Search by description</p>
            <p>• <strong>OCR:</strong> Search text within images (coming soon)</p>
            <p>• <strong>ASR:</strong> Search speech content (coming soon)</p>
            <p>• Results are sorted by similarity</p>
            <p>• Maximum 500 results per search</p>
          </div>
        </div>
      </div>
    </div>
  );
};
