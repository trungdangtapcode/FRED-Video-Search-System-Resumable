import React from 'react';
import type { SearchResult } from '@/types';
import { SearchService } from '@/services/searchService';
import { FrameTooltip } from '@/components/ui/frame-tooltip';

interface ResultsGridProps {
  results: SearchResult[];
  isLoading?: boolean;
  framesPerRow?: number;
}

export const ResultsGrid: React.FC<ResultsGridProps> = ({ 
  results, 
  isLoading, 
  framesPerRow = 10 
}) => {
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

  // Create dynamic grid class based on framesPerRow
  const getGridClass = () => {
    const baseClass = "grid gap-0";
    
    if (framesPerRow <= 4) return `${baseClass} grid-cols-4`;
    if (framesPerRow <= 6) return `${baseClass} grid-cols-6`;
    if (framesPerRow <= 8) return `${baseClass} grid-cols-8`;
    if (framesPerRow <= 10) return `${baseClass} grid-cols-10`;
    if (framesPerRow <= 12) return `${baseClass} grid-cols-12`;
    if (framesPerRow <= 15) return `${baseClass} grid-cols-[repeat(15,minmax(0,1fr))]`;
    return `${baseClass} grid-cols-[repeat(20,minmax(0,1fr))]`;
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className={getGridClass()}>
        {results.map((result, index) => (
          <div key={`${result.video_path}-${result.frame_idx}`}>
            <FrameTooltip
              frameData={result}
              frameIndex={index}
            >
              <div className="aspect-video bg-gray-200 hover:opacity-80 transition-opacity cursor-pointer group relative">
                <img
                  src={SearchService.getImageUrl(result.frame_path)}
                  alt={`Frame ${index + 1}`}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
                {/* Optional hover overlay with frame info for larger frames */}
                {framesPerRow <= 8 && (
                  <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <div className="text-white text-xs text-center p-2">
                      <div>#{index + 1}</div>
                      <div>{SearchService.formatTimestamp(result.timestamp)}</div>
                    </div>
                  </div>
                )}
              </div>
            </FrameTooltip>
          </div>
        ))}
      </div>
    </div>
  );
};
