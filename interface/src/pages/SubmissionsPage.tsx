import React, { useEffect, useState } from 'react';
import { submissionService } from '@/services/submissionService';
import type { QuestionSubmission } from '@/services/submissionService';
import { openVideoPlayer } from '@/utils/videoUtils';
import { extractVideoFrame } from '@/utils/videoFrameExtraction';
import { API_ENDPOINTS, ROOT_DIR } from '@/constants';
import { Film, Clock, Hash } from 'lucide-react';
import { ConfirmModal, AlertModal } from '@/components/ui/Modal';

interface GroupedSubmissions {
  question: string;
  frames: QuestionSubmission[];
}

// Component to extract and display frame from video
const FrameImage: React.FC<{
  frame: QuestionSubmission;
  onError?: () => void;
}> = ({ frame, onError }) => {
  const [imageSrc, setImageSrc] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const extractFrame = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Get video URL from static server
        const videoUrl = getVideoUrl(frame.video_path);
        console.log('Extracting frame from video:', videoUrl, 'at timestamp:', frame.timestamp);

        const frameDataUrl = await extractVideoFrame(videoUrl, frame.timestamp);
        setImageSrc(frameDataUrl);
      } catch (error) {
        console.error('Failed to extract frame:', error);
        setError('Failed to extract frame');
        if (onError) {
          onError();
        }
      } finally {
        setIsLoading(false);
      }
    };

    extractFrame();
  }, [frame.video_path, frame.timestamp, onError]);

  const getVideoUrl = (videoPath: string) => {
    // Remove the /root prefix and add the static server base URL
    const relativePath = videoPath.replace(ROOT_DIR, '');
    return `${API_ENDPOINTS.STATIC_SERVER}/${relativePath}`;
  };

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-300 text-gray-500 text-xs">
        <div className="animate-pulse">Loading...</div>
      </div>
    );
  }

  if (error || !imageSrc) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-300 text-gray-500 text-xs">
        <div className="text-center">
          Frame #{frame.frame_idx}<br/>
          <small>Failed to load</small>
        </div>
      </div>
    );
  }

  return (
    <img
      src={imageSrc}
      alt={`Frame ${frame.frame_idx}`}
      className="w-full h-full object-cover"
      loading="lazy"
    />
  );
};

const SubmissionsPage: React.FC = () => {
  const [submissions, setSubmissions] = useState<GroupedSubmissions[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleteMode, setIsDeleteMode] = useState(false);
  
  // Modal states
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
  }>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {}
  });
  
  const [alertModal, setAlertModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    type: 'success' | 'error' | 'info';
  }>({
    isOpen: false,
    title: '',
    message: '',
    type: 'info'
  });

  useEffect(() => {
    loadSubmissions();
  }, []);

  // Handle "X" key for delete mode
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ignore if typing in an input
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return;
      }

      if (event.key.toLowerCase() === 'x' && !event.ctrlKey && !event.metaKey) {
        console.log('X key pressed - entering delete mode');
        setIsDeleteMode(true);
      }
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() === 'x') {
        console.log('X key released - exiting delete mode');
        setIsDeleteMode(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
    };
  }, []);

  const loadSubmissions = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const allSubmissions = await submissionService.getAllSubmissions();
      
      // Convert the object to array format
      const groupedSubmissions: GroupedSubmissions[] = Object.entries(allSubmissions).map(
        ([question, frames]) => ({
          question,
          frames,
        })
      );

      setSubmissions(groupedSubmissions);
    } catch (error) {
      console.error('Error loading submissions:', error);
      setError('Failed to load submissions');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFrameClick = async (frame: QuestionSubmission, question: string) => {
    console.log('Frame clicked. Delete mode:', isDeleteMode);
    
    if (isDeleteMode) {
      console.log('In delete mode - deleting frame');
      
      // Show confirmation modal instead of native confirm
      setConfirmModal({
        isOpen: true,
        title: 'Delete Frame',
        message: `Are you sure you want to delete this frame from "${question}"?`,
        onConfirm: async () => {
          try {
            console.log('Deleting frame:', frame);
            await submissionService.deleteFrame({
              question: question,
              video_path: frame.video_path,
              timestamp: frame.timestamp,
              frame_idx: frame.frame_idx,
            });
            
            // Show success alert
            setAlertModal({
              isOpen: true,
              title: 'Success',
              message: 'Frame deleted successfully!',
              type: 'success'
            });
            
            // Reload submissions to reflect the change
            await loadSubmissions();
          } catch (error) {
            // Show error alert
            setAlertModal({
              isOpen: true,
              title: 'Error',
              message: 'Failed to delete frame. Please try again.',
              type: 'error'
            });
            console.error('Delete error:', error);
          }
        }
      });
    } else {
      console.log('Not in delete mode - opening video player');
      // Convert QuestionSubmission to SearchResult format for video player
      const searchResult = {
        video_path: frame.video_path,
        timestamp: frame.timestamp,
        frame_idx: frame.frame_idx,
        frame_path: '', // We'll generate this
        compressed_frame_path: '', // We'll generate this
        fps: 25, // Default FPS
      };
      
      openVideoPlayer(searchResult);
    }
  };

  const formatTimestamp = (timestamp: number) => {
    const minutes = Math.floor(timestamp / 60);
    const seconds = Math.floor(timestamp % 60);
    const milliseconds = Math.floor((timestamp % 1) * 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}.${milliseconds.toString().padStart(3, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg">Loading submissions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-red-600">{error}</div>
      </div>
    );
  }

  if (submissions.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">No submissions found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Submitted Frames</h1>
              <p className="text-gray-600 mt-1">
                {submissions.length} question{submissions.length !== 1 ? 's' : ''} with {' '}
                {submissions.reduce((total, group) => total + group.frames.length, 0)} frame{submissions.reduce((total, group) => total + group.frames.length, 0) !== 1 ? 's' : ''}
              </p>
            </div>
            {/* Delete mode indicator */}
            {isDeleteMode && (
              <div className="bg-red-500 text-white px-4 py-2 rounded-lg font-bold text-sm shadow-lg animate-pulse">
                DELETE MODE - Click frame to delete
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-6 space-y-8">
        {submissions.map((group) => (
          <div key={group.question} className="bg-white rounded-lg shadow-sm border p-6">
            {/* Question Header */}
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                {group.question}
              </h2>
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span className="flex items-center gap-1">
                  <Hash className="h-4 w-4" />
                  {group.frames.length} frame{group.frames.length !== 1 ? 's' : ''}
                </span>
              </div>
            </div>

            {/* Frames Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-4">
              {group.frames.map((frame) => (
                <div
                  key={`${frame.video_path}-${frame.frame_idx}`}
                  className={`group cursor-pointer ${
                    isDeleteMode ? 'ring-2 ring-red-400' : ''
                  }`}
                  onClick={() => handleFrameClick(frame, group.question)}
                >
                  <div className="aspect-video bg-gray-200 rounded-lg overflow-hidden hover:opacity-80 transition-opacity">
                    <FrameImage frame={frame} />
                  </div>
                  
                  {/* Frame Info */}
                  <div className="mt-2 space-y-1">
                    <div className="text-xs text-gray-600 flex items-center gap-1">
                      <Film className="h-3 w-3" />
                      {frame.video_path.split('/').pop()?.replace('.mp4', '')}
                    </div>
                    <div className="text-xs text-gray-500 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatTimestamp(frame.timestamp)}
                    </div>
                    <div className="text-xs text-gray-400">
                      Frame #{frame.frame_idx}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      
      {/* Modals */}
      <ConfirmModal
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal(prev => ({ ...prev, isOpen: false }))}
        onConfirm={confirmModal.onConfirm}
        title={confirmModal.title}
        message={confirmModal.message}
        confirmText="Delete"
        cancelText="Cancel"
        isDestructive={true}
      />
      
      <AlertModal
        isOpen={alertModal.isOpen}
        onClose={() => setAlertModal(prev => ({ ...prev, isOpen: false }))}
        title={alertModal.title}
        message={alertModal.message}
        type={alertModal.type}
      />
    </div>
  );
};

export default SubmissionsPage;
