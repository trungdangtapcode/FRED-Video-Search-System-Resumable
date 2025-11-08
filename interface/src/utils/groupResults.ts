import type { SearchResult, GroupedResults } from '@/types';

export const groupResultsByVideo = (results: SearchResult[]): GroupedResults[] => {
  const groupedMap = new Map<string, SearchResult[]>();
  
  // Group results by video path
  results.forEach(result => {
    const videoPath = result.video_path;
    if (!groupedMap.has(videoPath)) {
      groupedMap.set(videoPath, []);
    }
    groupedMap.get(videoPath)!.push(result);
  });
  
  // Convert to array and sort frames within each video by frame index
  return Array.from(groupedMap.entries()).map(([videoPath, frames]) => {
    const videoName = videoPath.split('/').pop()?.replace('.mp4', '') || 'Unknown';
    const sortedFrames = frames.sort((a, b) => a.frame_idx - b.frame_idx);
    
    return {
      videoPath,
      videoName,
      frames: sortedFrames
    };
  }).sort((a, b) => {
    // Sort videos by the similarity score of their first frame (original order)
    const aFirstIndex = results.findIndex(r => r.video_path === a.videoPath);
    const bFirstIndex = results.findIndex(r => r.video_path === b.videoPath);
    return aFirstIndex - bFirstIndex;
  });
};
