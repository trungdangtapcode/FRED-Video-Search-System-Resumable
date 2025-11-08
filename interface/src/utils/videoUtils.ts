import type { SearchResult } from '@/types';

export const openVideoPlayer = (videoData: SearchResult) => {
  // Encode the video data as URL parameter
  const encodedData = encodeURIComponent(JSON.stringify(videoData));
  
  // Create the URL for the video player page
  const videoPlayerUrl = `/video-player?data=${encodedData}`;
  
  // Open in new tab
  window.open(videoPlayerUrl, '_blank', 'noopener,noreferrer');
};

export const formatTimestamp = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
};

export const getVideoName = (videoPath: string): string => {
  return videoPath.split('/').pop() || 'Unknown Video';
};
