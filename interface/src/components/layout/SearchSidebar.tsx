import React, { useState } from 'react';
import { UnifiedSearchBox } from '@/components/search/UnifiedSearchBox';
import { MultiFrameSearchBox } from '@/components/search/MultiFrameSearchBox';
import { ImageSearchBox } from '@/components/search/ImageSearchBox';
import { useUnifiedSearch } from '@/hooks/useUnifiedSearch';
import { useMultiFrameSearch } from '@/hooks/useMultiFrameSearch';
import { useImageSearch } from '@/hooks/useImageSearch';
import type { SearchType } from '@/types';
import { Search, Layers, Image } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SearchSidebarProps {
  onSearchResults: (results: any[], searchType: SearchType) => void;
  onSearchStart?: () => void;
  onTopKChange?: (topK: number) => void;
}

export const SearchSidebar: React.FC<SearchSidebarProps> = ({ onSearchResults, onSearchStart, onTopKChange }) => {
  const { searchState, performSearch, clearResults } = useUnifiedSearch();
  const { searchState: multiFrameState, performSearch: performMultiFrameSearch, clearResults: clearMultiFrameResults } = useMultiFrameSearch();
  const { searchState: imageSearchState, performSearch: performImageSearch, clearResults: clearImageResults } = useImageSearch();
  const [searchMode, setSearchMode] = useState<'single' | 'multi' | 'image'>('single');

  const handleSearch = async (query: string, ocr: string, asr: string, topK: number) => {
    console.log('SearchSidebar: Starting unified search with:', { query, ocr, asr, topK });
    onSearchStart?.();
    onTopKChange?.(topK); // Report the current top_k value
    const results = await performSearch(query, ocr, asr, topK);
    console.log('SearchSidebar: Search completed, got', results.length, 'results');
    // Use 'text' as the search type for compatibility with existing display logic
    onSearchResults(results, 'text');
  };

  const handleMultiFrameSearch = async (frames: any[], topK: number) => {
    console.log('SearchSidebar: Starting multi-frame search with:', { frames, topK });
    onSearchStart?.();
    onTopKChange?.(topK); // Report the current top_k value
    const results = await performMultiFrameSearch(frames, topK);
    console.log('SearchSidebar: Multi-frame search completed, got', results.length, 'results');
    console.log('Sample results:', results);
    // Make sure result in results have fps field
    results.forEach((res, idx) => {
      if (!res.fps) {
        console.error(`Result at index ${idx} missing fps, setting default -1`);

        res.fps = -1;
      }
    });
    // Use 'text' as the search type for compatibility with existing display logic
    onSearchResults(results, 'text');
  };

  const handleImageSearch = async (imageFile: File, topK: number) => {
    console.log('SearchSidebar: Starting image search with:', { fileName: imageFile.name, topK });
    onSearchStart?.();
    onTopKChange?.(topK); // Report the current top_k value
    const results = await performImageSearch(imageFile, topK);
    console.log('SearchSidebar: Image search completed, got', results.length, 'results');
    // Set default fps for compatibility
    results.forEach((res, idx) => {
      if (!res.fps) {
        console.error(`Result at index ${idx} missing fps, setting default -1`);
        res.fps = -1;
      }
    });
    onSearchResults(results, 'text');
  };

  const handleClear = () => {
    if (searchMode === 'single') {
      clearResults();
    } else if (searchMode === 'multi') {
      clearMultiFrameResults();
    } else {
      clearImageResults();
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
              Text
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
            <Button
              variant={searchMode === 'image' ? 'default' : 'ghost'}
              size="sm"
              className="flex-1 h-7 text-xs"
              onClick={() => setSearchMode('image')}
            >
              <Image className="h-3 w-3 mr-1" />
              Image
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
          ) : searchMode === 'multi' ? (
            <MultiFrameSearchBox
              searchState={multiFrameState}
              onSearch={handleMultiFrameSearch}
              onClear={handleClear}
            />
          ) : (
            <ImageSearchBox
              onSearch={handleImageSearch}
              onClear={handleClear}
              isLoading={imageSearchState.isLoading}
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
            ) : searchMode === 'multi' ? (
              <>
                <p>• <strong>Multi-Frame:</strong> Describe 2-3 frames from the same video</p>
                <p>• <strong>Timestamps:</strong> Specify expected timing for each frame</p>
                <p>• <strong>Combined Scoring:</strong> Results ranked by total frame similarity</p>
                <p>• <strong>Temporal Weighting:</strong> Closer timestamps get higher scores</p>
                <p>• At least one frame must have content</p>
                <p>• Maximum 3 frames per search</p>
              </>
            ) : (
              <>
                <p>• <strong>Image Search:</strong> Upload an image to find similar frames</p>
                <p>• <strong>Visual Similarity:</strong> Uses computer vision to match content</p>
                <p>• <strong>Supported Formats:</strong> PNG, JPG, JPEG, GIF, BMP, WEBP</p>
                <p>• <strong>File Size:</strong> Maximum 10MB per image</p>
                <p>• <strong>AI Matching:</strong> Finds visually similar scenes and objects</p>
                <p>• Results ranked by visual similarity score</p>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
