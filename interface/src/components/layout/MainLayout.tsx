import React, { useState } from 'react';
import { SearchSidebar } from './SearchSidebar';
import { ResultsGrid } from '@/components/search/ResultsGrid';
import type { SearchResult, SearchType } from '@/types';

export const MainLayout: React.FC = () => {
  const [currentResults, setCurrentResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);

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
      <div className="flex-1 overflow-hidden">
        <ResultsGrid 
          results={currentResults} 
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};
