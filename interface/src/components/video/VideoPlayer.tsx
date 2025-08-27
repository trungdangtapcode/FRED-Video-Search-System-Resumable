import React, { useRef, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Play, Pause, Volume2, VolumeX, RotateCcw, Maximize } from 'lucide-react';
import { API_ENDPOINTS } from '@/constants';
import type { SearchResult } from '@/types';

interface VideoPlayerProps {
  videoData: SearchResult;
  autoplay?: boolean;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({ 
  videoData, 
  autoplay = true 
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Get video URL from static server
  const getVideoUrl = (videoPath: string) => {
    // Remove the /root prefix and add the static server base URL
    const relativePath = videoPath.replace('/root/', '');
    return `${API_ENDPOINTS.STATIC_SERVER}/${relativePath}`;
  };

  // Format time display with milliseconds
  const formatTime = (timeInSeconds: number) => {
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = Math.floor(timeInSeconds % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Format time display with milliseconds for real-time display
  const formatTimeWithMilliseconds = (timeInSeconds: number) => {
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = Math.floor(timeInSeconds % 60);
    const milliseconds = Math.floor((timeInSeconds % 1) * 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}.${milliseconds.toString().padStart(3, '0')}`;
  };

  // Calculate current frame index from timestamp and fps
  const calculateFrameIndex = (timeInSeconds: number, fps: number) => {
    return Math.floor(timeInSeconds * fps);
  };

  // Initialize video
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleLoadedMetadata = () => {
      setDuration(video.duration);
      // Jump to the timestamp from the search result
      if (videoData.timestamp) {
        video.currentTime = videoData.timestamp;
        setCurrentTime(videoData.timestamp);
      }
      
      if (autoplay) {
        video.play().then(() => {
          setIsPlaying(true);
        }).catch(error => {
          console.error('Autoplay failed:', error);
        });
      }
    };

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
    };

    const handleEnded = () => {
      setIsPlaying(false);
    };

    // Add more frequent time updates for millisecond precision
    let rafId: number;
    const updateTimeHighFrequency = () => {
      if (video && !video.paused) {
        setCurrentTime(video.currentTime);
      }
      rafId = requestAnimationFrame(updateTimeHighFrequency);
    };

    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('ended', handleEnded);
    video.addEventListener('play', () => {
      rafId = requestAnimationFrame(updateTimeHighFrequency);
    });
    video.addEventListener('pause', () => {
      if (rafId) {
        cancelAnimationFrame(rafId);
      }
    });

    return () => {
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('ended', handleEnded);
      if (rafId) {
        cancelAnimationFrame(rafId);
      }
    };
  }, [videoData.timestamp, autoplay]);

  // Play/Pause toggle
  const togglePlayPause = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
      setIsPlaying(false);
    } else {
      video.play().then(() => {
        setIsPlaying(true);
      }).catch(error => {
        console.error('Play failed:', error);
      });
    }
  };

  // Seek to position
  const handleSeek = (value: number[]) => {
    const video = videoRef.current;
    if (!video) return;

    const newTime = value[0];
    video.currentTime = newTime;
    setCurrentTime(newTime);
  };

  // Volume control
  const handleVolumeChange = (value: number[]) => {
    const video = videoRef.current;
    if (!video) return;

    const newVolume = value[0];
    video.volume = newVolume;
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
  };

  // Mute toggle
  const toggleMute = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isMuted) {
      video.volume = volume > 0 ? volume : 0.5;
      setIsMuted(false);
    } else {
      video.volume = 0;
      setIsMuted(true);
    }
  };

  // Jump to frame timestamp
  const jumpToFrameTime = () => {
    const video = videoRef.current;
    if (!video || !videoData.timestamp) return;

    video.currentTime = videoData.timestamp;
    setCurrentTime(videoData.timestamp);
  };

  // Fullscreen toggle
  const toggleFullscreen = () => {
    const video = videoRef.current;
    if (!video) return;

    if (!isFullscreen) {
      if (video.requestFullscreen) {
        video.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  // Handle fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  return (
    <div className="w-full h-screen bg-black flex flex-col">
      {/* Header Info Bar */}
      <div className="bg-gray-900 text-white p-3 flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-lg font-semibold">Video Player</h1>
          <p className="text-sm text-gray-300">{videoData.video_path.split('/').pop()}</p>
        </div>
        <div className="text-center flex-1">
          {/* Real-time timestamp with milliseconds and frame index */}
          <div className="text-4xl font-mono font-bold text-yellow-400 bg-gray-800 px-6 py-3 rounded-lg border-2 border-yellow-500 shadow-lg inline-block">
            <span className="drop-shadow-lg">
              {formatTimeWithMilliseconds(currentTime)} <span className="text-green-400">({calculateFrameIndex(currentTime, videoData.fps)})</span>
            </span>
          </div>
          <div className="text-xs text-gray-400 mt-1">
            Current Time (Frame Index)
          </div>
        </div>
        <div className="text-sm text-gray-300">
          Start Frame: {formatTime(videoData.timestamp)}
        </div>
      </div>

      {/* Video Element */}
      <div className="flex-1 bg-black flex items-center justify-center min-h-0">
        <video
          ref={videoRef}
          className="w-full h-full object-contain"
          controls={false}
          preload="metadata"
          onClick={togglePlayPause}
        >
          <source src={getVideoUrl(videoData.video_path)} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
      </div>

      {/* Controls */}
      <div className="bg-gray-900 p-4 space-y-3 flex-shrink-0">
        {/* Progress Bar */}
        <div className="space-y-1">
          <Slider
            value={[currentTime]}
            max={duration}
            step={0.1}
            onValueChange={handleSeek}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-300">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={togglePlayPause}
              className="bg-gray-800 border-gray-600 text-white hover:bg-gray-700"
            >
              {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={jumpToFrameTime}
              title="Jump to frame timestamp"
              className="bg-gray-800 border-gray-600 text-white hover:bg-gray-700"
            >
              <RotateCcw className="h-4 w-4" />
            </Button>
          </div>

          <div className="flex items-center gap-2">
            {/* Volume Control */}
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleMute}
                className="text-white hover:bg-gray-700"
              >
                {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
              </Button>
              <Slider
                value={[isMuted ? 0 : volume]}
                max={1}
                step={0.1}
                onValueChange={handleVolumeChange}
                className="w-20"
              />
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={toggleFullscreen}
              className="bg-gray-800 border-gray-600 text-white hover:bg-gray-700"
            >
              <Maximize className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Frame Info */}
        <div className="text-xs text-gray-300 bg-gray-800 p-2 rounded">
          <div className="grid grid-cols-4 gap-2">
            <div>Frame: {videoData.frame_idx}</div>
            <div>FPS: {videoData.fps}</div>
            <div>Timestamp: {formatTime(videoData.timestamp)}</div>
            <div>Video: {videoData.video_path.split('/').pop()}</div>
          </div>
        </div>
      </div>
    </div>
  );
};
