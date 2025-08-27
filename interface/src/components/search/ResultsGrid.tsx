import React from 'react';
import type { SearchResult, DisplayMode } from '@/types';
import { SearchService } from '@/services/searchService';
import { FrameTooltip } from '@/components/ui/frame-tooltip';
import { groupResultsByVideo } from '@/utils/groupResults';
import { openVideoPlayer } from '@/utils/videoUtils';
import { Film } from 'lucide-react';

interface ResultsGridProps {
  results: SearchResult[];
  isLoading?: boolean;
  framesPerRow?: number;
  displayMode?: DisplayMode;
}

// Component for grouped results view
const GroupedResultsView: React.FC<{ results: SearchResult[]; framesPerRow: number }> = ({ 
  results, 
  framesPerRow 
}) => {
  const groupedResults = groupResultsByVideo(results);

  // Create dynamic grid class based on framesPerRow (same as main grid)
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
    <div className="h-full overflow-y-auto p-4 space-y-6">
      {groupedResults.map((group, groupIndex) => (
        <div key={group.videoPath} className="space-y-2">
          {/* Video Header */}
          <div className="flex items-center gap-2 pb-2">
            <Film className="h-4 w-4 text-blue-500" />
            <h3 className="text-sm font-medium text-gray-900">
              {group.videoName}
            </h3>
            <span className="text-xs text-gray-500">
              ({group.frames.length} frame{group.frames.length !== 1 ? 's' : ''})
            </span>
          </div>
          
          {/* Frames Grid - Always use the same grid layout regardless of frame count */}
          <div className={getGridClass()}>
            {group.frames.map((result, frameIndex) => {
              const globalIndex = results.findIndex(r => 
                r.video_path === result.video_path && r.frame_idx === result.frame_idx
              );
              return (
                <div key={`${result.video_path}-${result.frame_idx}-${result.frame_idx}`}>
                  <FrameTooltip frameData={result} frameIndex={globalIndex}>
                    <div 
                      className="aspect-video bg-gray-200 hover:opacity-80 transition-opacity cursor-pointer"
                      onClick={() => openVideoPlayer(result)}
                    >
                      <img
                        src={SearchService.getImageUrl(result.frame_path)}
                        alt={`Frame ${frameIndex + 1} from ${group.videoName}`}
                        className="w-full h-full object-cover"
                        loading="lazy"
                      />
                    </div>
                  </FrameTooltip>
                </div>
              );
            })}
            {/* Fill empty slots if needed to maintain grid structure */}
            {Array.from({ length: Math.max(0, framesPerRow - group.frames.length) }).map((_, emptyIndex) => (
              <div key={`empty-${emptyIndex}`} className="aspect-video bg-gray-100"></div>
            ))}
          </div>
          
          {/* Separator line (except for last group) */}
          {groupIndex < groupedResults.length - 1 && (
            <div className="border-b border-gray-200 mt-4"></div>
          )}
        </div>
      ))}
    </div>
  );
};

export const ResultsGrid: React.FC<ResultsGridProps> = ({ 
  results, 
  isLoading, 
  framesPerRow = 10,
  displayMode = 'all'
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

  // Render based on display mode
  if (displayMode === 'grouped') {
    return <GroupedResultsView results={results} framesPerRow={framesPerRow} />;
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
              <div 
                className="aspect-video bg-gray-200 hover:opacity-80 transition-opacity cursor-pointer group relative"
                onClick={() => openVideoPlayer(result)}
              >
                <img
                  src={SearchService.getImageUrl(result.compressed_frame_path)}
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
