import React, { useState } from 'react';
import { SearchSidebar } from './SearchSidebar';
import { TopBar } from './TopBar';
import { ResultsGrid } from '@/components/search/ResultsGrid';
import type { SearchResult, SearchType, DisplayMode } from '@/types';

export const MainLayout: React.FC = () => {
  const [currentResults, setCurrentResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [framesPerRow, setFramesPerRow] = useState(10);
  const [displayMode, setDisplayMode] = useState<DisplayMode>('all');

  const handleSearchResults = (results: SearchResult[], searchType: SearchType) => {
    console.log('MainLayout: Received search results:', results.length, 'results for', searchType);
    setCurrentResults(results);
    setIsLoading(false);
  };

  const handleSearchStart = () => {
    console.log('MainLayout: Search started');
    setIsLoading(true);
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <SearchSidebar onSearchResults={handleSearchResults} onSearchStart={handleSearchStart} />
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <TopBar 
          framesPerRow={framesPerRow}
          onFramesPerRowChange={setFramesPerRow}
          totalResults={currentResults.length}
          displayMode={displayMode}
          onDisplayModeChange={setDisplayMode}
        />
        
        {/* Results Grid */}
        <div className="flex-1 overflow-hidden">
          <ResultsGrid 
            results={currentResults} 
            isLoading={isLoading}
            framesPerRow={framesPerRow}
            displayMode={displayMode}
          />
        </div>
      </div>
    </div>
  );
};
