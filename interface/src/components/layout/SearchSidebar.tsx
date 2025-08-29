import React, { useState } from 'react';
import { UnifiedSearchBox } from '@/components/search/UnifiedSearchBox';
import { MultiFrameSearchBox } from '@/components/search/MultiFrameSearchBox';
import { useUnifiedSearch } from '@/hooks/useUnifiedSearch';
import { useMultiFrameSearch } from '@/hooks/useMultiFrameSearch';
import type { SearchType } from '@/types';
import { Search, Layers } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SearchSidebarProps {
  onSearchResults: (results: any[], searchType: SearchType) => void;
  onSearchStart?: () => void;
}

export const SearchSidebar: React.FC<SearchSidebarProps> = ({ onSearchResults, onSearchStart }) => {
  const { searchState, performSearch, clearResults } = useUnifiedSearch();
  const { searchState: multiFrameState, performSearch: performMultiFrameSearch, clearResults: clearMultiFrameResults } = useMultiFrameSearch();
  const [searchMode, setSearchMode] = useState<'single' | 'multi'>('single');

  const handleSearch = async (query: string, ocr: string, asr: string, topK: number) => {
    console.log('SearchSidebar: Starting unified search with:', { query, ocr, asr, topK });
    onSearchStart?.();
    const results = await performSearch(query, ocr, asr, topK);
    console.log('SearchSidebar: Search completed, got', results.length, 'results');
    // Use 'text' as the search type for compatibility with existing display logic
    onSearchResults(results, 'text');
  };

  const handleMultiFrameSearch = async (frames: any[], topK: number) => {
    console.log('SearchSidebar: Starting multi-frame search with:', { frames, topK });
    onSearchStart?.();
    const results = await performMultiFrameSearch(frames, topK);
    console.log('SearchSidebar: Multi-frame search completed, got', results.length, 'results');
    // Use 'text' as the search type for compatibility with existing display logic
    onSearchResults(results, 'text');
  };

  const handleClear = () => {
    if (searchMode === 'single') {
      clearResults();
    } else {
      clearMultiFrameResults();
    }
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

        {/* Search Mode Toggle */}
        <div className="mb-4">
          <div className="flex rounded-lg bg-muted p-1">
            <Button
              variant={searchMode === 'single' ? 'default' : 'ghost'}
              size="sm"
              className="flex-1 h-7 text-xs"
              onClick={() => setSearchMode('single')}
            >
              <Search className="h-3 w-3 mr-1" />
              Single
            </Button>
            <Button
              variant={searchMode === 'multi' ? 'default' : 'ghost'}
              size="sm"
              className="flex-1 h-7 text-xs"
              onClick={() => setSearchMode('multi')}
            >
              <Layers className="h-3 w-3 mr-1" />
              Multi
            </Button>
          </div>
        </div>

        {/* Search Box */}
        <div className="space-y-3">
          {searchMode === 'single' ? (
            <UnifiedSearchBox
              searchState={searchState}
              onSearch={handleSearch}
              onClear={handleClear}
            />
          ) : (
            <MultiFrameSearchBox
              searchState={multiFrameState}
              onSearch={handleMultiFrameSearch}
              onClear={handleClear}
            />
          )}
        </div>

        {/* Info Section */}
        <div className="mt-8 p-4 bg-muted/50 rounded-lg">
          <h3 className="text-sm font-medium mb-2">Search Information</h3>
          <div className="text-xs text-muted-foreground space-y-1">
            {searchMode === 'single' ? (
              <>
                <p>• <strong>Text Query:</strong> Search by description</p>
                <p>• <strong>OCR:</strong> Search text within images</p>
                <p>• <strong>ASR:</strong> Search speech content</p>
                <p>• At least one field must be filled</p>
                <p>• Results are sorted by similarity</p>
                <p>• Maximum 500 results per search</p>
              </>
            ) : (
              <>
                <p>• <strong>Multi-Frame:</strong> Describe 2-3 frames from the same video</p>
                <p>• <strong>Timestamps:</strong> Specify expected timing for each frame</p>
                <p>• <strong>Combined Scoring:</strong> Results ranked by total frame similarity</p>
                <p>• <strong>Temporal Weighting:</strong> Closer timestamps get higher scores</p>
                <p>• At least one frame must have content</p>
                <p>• Maximum 3 frames per search</p>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
