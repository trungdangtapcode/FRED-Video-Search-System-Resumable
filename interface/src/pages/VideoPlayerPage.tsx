import React, { useEffect, useState } from 'react';
import { VideoPlayer } from '@/components/video/VideoPlayer';
import type { SearchResult } from '@/types';

const VideoPlayerPage: React.FC = () => {
  const [videoData, setVideoData] = useState<SearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Get video data from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const videoDataParam = urlParams.get('data');
    
    if (videoDataParam) {
      try {
        const decodedData = decodeURIComponent(videoDataParam);
        const parsedData = JSON.parse(decodedData);
        setVideoData(parsedData);
        console.log('Video data loaded:', parsedData);
      } catch (err) {
        setError('Failed to parse video data from URL');
        console.error('Error parsing video data:', err);
      }
    } else {
      setError('No video data provided');
    }
  }, []);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-2">Error</h1>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  if (!videoData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading video...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="video-player-page h-screen w-screen bg-black overflow-hidden">
      <VideoPlayer videoData={videoData} autoplay={true} />
    </div>
  );
};

export default VideoPlayerPage;
