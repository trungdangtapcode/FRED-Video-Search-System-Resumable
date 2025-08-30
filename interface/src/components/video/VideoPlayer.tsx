import React, { useRef, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Play, Pause, Volume2, VolumeX, RotateCcw, Maximize } from 'lucide-react';
import { API_ENDPOINTS, ROOT_DIR } from '@/constants';
import { SubmitFrameButton } from './SubmitFrameButton';
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
  const [playbackRate, setPlaybackRate] = useState(1);
  const [isSpeedHeld, setIsSpeedHeld] = useState(false);
  const [normalSpeed, setNormalSpeed] = useState(1);
  const [speedKeyTimer, setSpeedKeyTimer] = useState<NodeJS.Timeout | null>(null);
  const [isSpeedKeyPressed, setIsSpeedKeyPressed] = useState(false);
  const [currentSpeedKey, setCurrentSpeedKey] = useState<string | null>(null);

  // Get video URL from static server
  const getVideoUrl = (videoPath: string) => {
    // Remove the /root prefix and add the static server base URL
    const relativePath = videoPath.replace(ROOT_DIR, '');
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
    if (!video) {
      return;
    }

    const handleLoadedMetadata = () => {
      setDuration(video.duration);
      // Set initial playback rate
      video.playbackRate = playbackRate;
      
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
    if (!video) {
      return;
    }
    

    // if (isPlaying) {
    if (!!(video && !video.paused && !video.ended && video.readyState > 2)) {
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
    if (!video) {
      return;
    }

    const newTime = value[0];
    video.currentTime = newTime;
    setCurrentTime(newTime);
  };

  // Volume control
  const handleVolumeChange = (value: number[]) => {
    const video = videoRef.current;
    if (!video) {
      return;
    }

    const newVolume = value[0];
    video.volume = newVolume;
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
  };

  // Mute toggle
  const toggleMute = () => {
    const video = videoRef.current;
    if (!video) {
      return;
    }

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
    if (!video || !videoData.timestamp) {
      return;
    }

    video.currentTime = videoData.timestamp;
    setCurrentTime(videoData.timestamp);
  };

  // Fullscreen toggle
  const toggleFullscreen = () => {
    const video = videoRef.current;
    if (!video) {
      return;
    }

    if (!isFullscreen) {
      if (video.requestFullscreen) {
        video.requestFullscreen();
      }
    } else if (document.exitFullscreen) {
      document.exitFullscreen();
    }
  };

  // Playback speed control
  const changePlaybackSpeed = (speed: number) => {
    const video = videoRef.current;
    if (!video) {
      return;
    }

    video.playbackRate = speed;
    setPlaybackRate(speed);
  };

  // Common playback speeds
  const playbackSpeeds = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 3, 4, 5];

  const cyclePlaybackSpeed = () => {
    const currentIndex = playbackSpeeds.indexOf(playbackRate);
    const nextIndex = (currentIndex + 1) % playbackSpeeds.length;
    changePlaybackSpeed(playbackSpeeds[nextIndex]);
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

  // "." and "," key hold detection for 2x speed
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ignore if typing in an input
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (event.code) {
        case 'Comma': // "," key
          console.log('Comma key pressed - starting 2x speed');
          event.preventDefault();
          if (!isSpeedKeyPressed || currentSpeedKey !== event.code) {
            console.log('Starting speed boost timer');
            setIsSpeedKeyPressed(true);
            setCurrentSpeedKey(event.code);
            // Immediately activate 2x speed (no timer)
            setIsSpeedHeld(true);
            setNormalSpeed(playbackRate);
            changePlaybackSpeed(2);
          }
          break;
        case 'Space':
          event.preventDefault();
          togglePlayPause();
          break;
        case 'ArrowLeft':
          event.preventDefault();
          handleSeek([Math.max(0, currentTime - 10)]);
          break;
        case 'ArrowRight':
          event.preventDefault();
          handleSeek([Math.min(duration, currentTime + 10)]);
          break;
        case 'ArrowUp':
          event.preventDefault();
          handleVolumeChange([Math.min(1, volume + 0.1)]);
          break;
        case 'ArrowDown':
          event.preventDefault();
          handleVolumeChange([Math.max(0, volume - 0.1)]);
          break;
        case 'KeyM':
          event.preventDefault();
          toggleMute();
          break;
        case 'KeyF':
          event.preventDefault();
          toggleFullscreen();
          break;
        case 'KeyS':
          event.preventDefault();
          cyclePlaybackSpeed();
          break;
        case 'Digit1':
          event.preventDefault();
          changePlaybackSpeed(1);
          break;
        case 'Digit2':
          event.preventDefault();
          changePlaybackSpeed(2);
          break;
        case 'Digit0':
          event.preventDefault();
          changePlaybackSpeed(0.5);
          break;
        case 'Digit3':
          event.preventDefault();
          changePlaybackSpeed(3);
          break;
        case 'Digit4':
          event.preventDefault();
          changePlaybackSpeed(4);
          break;
        case 'Digit5':
          event.preventDefault();
          changePlaybackSpeed(5);
          break;
      }

      // Handle Ctrl+S for submit
      if (event.ctrlKey && event.key === 's') {
        event.preventDefault(); // Prevent browser's save dialog
        // Trigger submit frame functionality
        const submitButton = document.querySelector('[data-submit-frame-button]') as HTMLButtonElement;
        if (submitButton) {
          submitButton.click();
        }
      }
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.code === 'Comma') {
        console.log('Comma key released - stopping 2x speed');
        event.preventDefault();
        
        // Only handle if this was the key being pressed
        if (currentSpeedKey === event.code) {
          setIsSpeedKeyPressed(false);
          setCurrentSpeedKey(null);
          
          // Clear the hold timer
          if (speedKeyTimer) {
            clearTimeout(speedKeyTimer);
            setSpeedKeyTimer(null);
          }

          if (isSpeedHeld) {
            console.log('Restoring normal speed from', playbackRate, 'to', normalSpeed);
            // If was held, restore normal speed
            setIsSpeedHeld(false);
            changePlaybackSpeed(normalSpeed);
          }
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
      if (speedKeyTimer) {
        clearTimeout(speedKeyTimer);
      }
    };
  }, [isSpeedKeyPressed, isSpeedHeld, speedKeyTimer, currentSpeedKey, playbackRate, normalSpeed, currentTime, duration, volume]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (speedKeyTimer) {
        clearTimeout(speedKeyTimer);
      }
    };
  }, [speedKeyTimer]);

  // 2x speed button handlers
  const handleSpeedBoostMouseDown = () => {
    setIsSpeedHeld(true);
    setNormalSpeed(playbackRate);
    changePlaybackSpeed(2);
  };

  const handleSpeedBoostMouseUp = () => {
    setIsSpeedHeld(false);
    changePlaybackSpeed(normalSpeed);
  };

  return (
    <div className="w-full h-screen bg-black flex flex-col">
      {/* Header Info Bar */}
      <div className="bg-gray-900 text-white p-2 flex items-center justify-between flex-shrink-0">
        <div className="text-xs text-gray-300">
          {videoData.video_path.split('/').pop()}
        </div>
        <div className="text-center flex-1">
          {/* Real-time timestamp with milliseconds and frame index */}
          <div className="text-2xl font-mono font-bold text-yellow-400 bg-gray-800 px-4 py-1 rounded border border-yellow-500 inline-block">
            {formatTimeWithMilliseconds(currentTime)} <span className="text-green-400">({calculateFrameIndex(currentTime, videoData.fps)})</span>
          </div>
          {/* Playback speed indicator */}
          <span className="ml-3 text-sm font-semibold text-blue-400 bg-gray-800 px-2 py-1 rounded border border-blue-500">
            {isSpeedHeld ? '2x (HOLD)' : `${playbackRate}x`}
          </span>
        </div>
        <div className="text-xs text-gray-300">
          FPS: {videoData.fps}
        </div>
      </div>

      {/* Video Element */}
      <div className="flex-1 bg-black flex items-center justify-center min-h-0 relative">
        <video
          ref={videoRef}
          className="w-full h-full object-contain cursor-pointer"
          controls={false}
          preload="metadata"
          onClick={togglePlayPause}
        >
          <source src={getVideoUrl(videoData.video_path)} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
        
        {/* Speed boost indicator */}
        {isSpeedHeld && (
          <div className="absolute top-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-lg font-bold text-lg border-2 border-blue-400 shadow-lg animate-pulse">
            2x SPEED
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="bg-gray-900 p-3 space-y-2 flex-shrink-0">
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

            {/* Playback Speed Control */}
            <Button
              variant="outline"
              size="sm"
              onClick={cyclePlaybackSpeed}
              title="Change playback speed"
              className="bg-gray-800 border-gray-600 text-white hover:bg-gray-700 min-w-[50px]"
            >
              {playbackRate}x
            </Button>

            {/* 2x Speed Boost Button (Hold) */}
            <Button
              variant="outline"
              size="sm"
              onMouseDown={handleSpeedBoostMouseDown}
              onMouseUp={handleSpeedBoostMouseUp}
              onMouseLeave={handleSpeedBoostMouseUp}
              onTouchStart={handleSpeedBoostMouseDown}
              onTouchEnd={handleSpeedBoostMouseUp}
              title="Hold for 2x speed"
              className={`border-gray-600 text-white hover:bg-orange-600 min-w-[60px] ${
                isSpeedHeld ? 'bg-orange-600 border-orange-400' : 'bg-gray-800'
              }`}
            >
              {isSpeedHeld ? '2x!' : 'HOLD'}
            </Button>

            {/* Submit Frame Button */}
            <SubmitFrameButton 
              videoData={videoData}
              currentTime={currentTime}
              fps={videoData.fps}
            />
          </div>

          <div className="flex items-center gap-2">
            {/* Playback Speed Selector */}
            <select
              value={playbackRate}
              onChange={(e) => changePlaybackSpeed(Number(e.target.value))}
              className="bg-gray-800 border border-gray-600 text-white text-xs rounded px-2 py-1 hover:bg-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {playbackSpeeds.map((speed) => (
                <option key={speed} value={speed}>
                  {speed}x
                </option>
              ))}
            </select>
            
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
                className="w-16"
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
      </div>
    </div>
  );
};
