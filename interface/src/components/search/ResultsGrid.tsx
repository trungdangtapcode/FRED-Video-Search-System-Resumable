import React from 'react';
import type { SearchResult } from '@/types';
import { SearchService } from '@/services/searchService';

interface ResultsGridProps {
  results: SearchResult[];
  isLoading?: boolean;
}

export const ResultsGrid: React.FC<ResultsGridProps> = ({ results, isLoading }) => {
  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-lg">Searching...</div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        No results found
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="grid grid-cols-8 lg:grid-cols-9 xl:grid-cols-10 2xl:grid-cols-12 gap-0">
        {results.map((result, index) => (
          <div
            key={`${result.video_path}-${result.frame_idx}`}
            className="aspect-video bg-gray-200 hover:opacity-80 transition-opacity cursor-pointer"
          >
            <img
              src={SearchService.getImageUrl(result.frame_path)}
              alt={`Frame ${index + 1}`}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          </div>
        ))}
      </div>
    </div>
  );
};
