import React, { useEffect, useState } from 'react';
import { submissionService } from '@/services/submissionService';
import type { QuestionSubmission } from '@/services/submissionService';
import { openVideoPlayer } from '@/utils/videoUtils';
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

        // Remove ROOT_DIR from video path before sending to backend
        const relativePath = frame.video_path.replace(ROOT_DIR, '');
        // alert('Relative path: ' + frame.video_path);
        
        // Use backend extract_frame endpoint instead of client-side extraction
        const extractUrl = `${API_ENDPOINTS.SUBMIT_SERVER}/extract_frame?video_path=${encodeURIComponent(relativePath)}&timestamp=${frame.timestamp}`;
        console.log('Extracting frame from backend:', extractUrl);

        const response = await fetch(extractUrl);
        if (!response.ok) {
          throw new Error(`Failed to extract frame: ${response.statusText}`);
        }

        // Convert response to blob and create object URL
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        setImageSrc(imageUrl);
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
    
    // Cleanup function to revoke object URL when component unmounts
    return () => {
      if (imageSrc && imageSrc.startsWith('blob:')) {
        URL.revokeObjectURL(imageSrc);
      }
    };
  }, [frame.video_path, frame.timestamp, onError]);

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
  const [isReorderMode, setIsReorderMode] = useState(false);
  
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

  // Reorder modal state
  const [reorderModal, setReorderModal] = useState<{
    isOpen: boolean;
    frame: QuestionSubmission | null;
    question: string;
    currentIndex: number;
    totalFrames: number;
  }>({
    isOpen: false,
    frame: null,
    question: '',
    currentIndex: 0,
    totalFrames: 0
  });

  useEffect(() => {
    loadSubmissions();
  }, []);

  // Handle "X" key for delete mode and "C" key for reorder mode
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

      if (event.key.toLowerCase() === 'c' && !event.ctrlKey && !event.metaKey) {
        console.log('C key pressed - entering reorder mode');
        setIsReorderMode(true);
      }
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() === 'x') {
        console.log('X key released - exiting delete mode');
        setIsDeleteMode(false);
      }

      if (event.key.toLowerCase() === 'c') {
        console.log('C key released - exiting reorder mode');
        setIsReorderMode(false);
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

  const handleReorderFrame = async (newPosition: number) => {
    const { frame, question, currentIndex } = reorderModal;
    if (!frame) return;

    try {
      // Find the question group
      const questionGroup = submissions.find(s => s.question === question);
      if (!questionGroup) return;

      // Create new frames array with the frame moved to new position
      const newFrames = [...questionGroup.frames];
      
      // Remove frame from current position
      const [movedFrame] = newFrames.splice(currentIndex, 1);
      
      // Insert frame at new position
      newFrames.splice(newPosition, 0, movedFrame);

      // Update the submissions state locally
      const updatedSubmissions = submissions.map(s => 
        s.question === question 
          ? { ...s, frames: newFrames }
          : s
      );
      setSubmissions(updatedSubmissions);

      // Call backend to update the order
      await submissionService.reorderFrames(question, newFrames);

      setAlertModal({
        isOpen: true,
        title: 'Success',
        message: 'Frame order updated successfully!',
        type: 'success'
      });

      setReorderModal({ isOpen: false, frame: null, question: '', currentIndex: 0, totalFrames: 0 });
    } catch (error) {
      setAlertModal({
        isOpen: true,
        title: 'Error',
        message: 'Failed to reorder frame. Please try again.',
        type: 'error'
      });
      console.error('Reorder error:', error);
      
      // Reload submissions to reset state
      await loadSubmissions();
    }
  };

  const handleFrameClick = async (frame: QuestionSubmission, question: string) => {
    console.log('Frame clicked. Delete mode:', isDeleteMode, 'Reorder mode:', isReorderMode);
    
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
    } else if (isReorderMode) {
      console.log('In reorder mode - showing reorder dialog');
      
      // Find the current question's frames and the index of the clicked frame
      const questionGroup = submissions.find(s => s.question === question);
      if (!questionGroup) return;
      
      const currentIndex = questionGroup.frames.findIndex(f => 
        f.video_path === frame.video_path && 
        f.timestamp === frame.timestamp && 
        f.frame_idx === frame.frame_idx
      );
      
      if (currentIndex === -1) return;
      
      setReorderModal({
        isOpen: true,
        frame: frame,
        question: question,
        currentIndex: currentIndex,
        totalFrames: questionGroup.frames.length
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
        fps: frame.frame_idx/frame.timestamp, // Default FPS
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
            <div className="flex gap-2">
              {/* Delete mode indicator */}
              {isDeleteMode && (
                <div className="bg-red-500 text-white px-4 py-2 rounded-lg font-bold text-sm shadow-lg animate-pulse">
                  DELETE MODE - Click frame to delete
                </div>
              )}
              {/* Reorder mode indicator */}
              {isReorderMode && (
                <div className="bg-blue-500 text-white px-4 py-2 rounded-lg font-bold text-sm shadow-lg animate-pulse">
                  REORDER MODE - Click frame to change position
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-6 space-y-8">
        {submissions.sort((a, b) =>
  a.question.localeCompare(b.question)
).map((group) => (
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
              {group.frames.map((frame, index) => (
                <div
                  key={`${frame.video_path}-${frame.frame_idx}`}
                  className={`group cursor-pointer relative ${
                    isDeleteMode ? 'ring-2 ring-red-400' : ''
                  } ${
                    isReorderMode ? 'ring-2 ring-blue-400' : ''
                  }`}
                  onClick={() => handleFrameClick(frame, group.question)}
                >
                  <div className="aspect-video bg-gray-200 rounded-lg overflow-hidden hover:opacity-80 transition-opacity">
                    <FrameImage frame={frame} />
                  </div>
                  
                  {/* Frame position indicator for reorder mode */}
                  {isReorderMode && (
                    <div className="absolute top-1 left-1 bg-blue-500 text-white text-xs font-bold px-2 py-1 rounded">
                      {index + 1}
                    </div>
                  )}
                  
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
                    {/* Answer display if available */}
                    {frame.answer && (
                      <div className="text-xs text-green-600 bg-green-50 p-1 rounded mt-1">
                        <strong>A:</strong> {frame.answer.length > 50 ? `${frame.answer.substring(0, 50)}...` : frame.answer}
                      </div>
                    )}
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

      {/* Reorder Modal */}
      {reorderModal.isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw] border shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Reorder Frame</h3>
              <button
                onClick={() => setReorderModal({ isOpen: false, frame: null, question: '', currentIndex: 0, totalFrames: 0 })}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            {/* Frame Info */}
            <div className="bg-gray-100 rounded p-3 mb-4 text-sm text-gray-700">
              <div className="font-mono">
                <div>Question: {reorderModal.question}</div>
                <div>Current Position: {reorderModal.currentIndex + 1} of {reorderModal.totalFrames}</div>
                <div>Video: {reorderModal.frame?.video_path.split('/').pop()}</div>
                <div>Timestamp: {reorderModal.frame ? formatTimestamp(reorderModal.frame.timestamp) : ''}</div>
              </div>
            </div>

            {/* Position Input */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                New Position (1-{reorderModal.totalFrames}):
              </label>
              <input
                type="number"
                min="1"
                max={reorderModal.totalFrames}
                defaultValue={reorderModal.currentIndex + 1}
                className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                id="new-position"
              />
            </div>

            {/* Quick Position Buttons */}
            <div className="mb-4">
              <div className="text-sm font-medium text-gray-700 mb-2">Quick Actions:</div>
              <div className="flex gap-2 flex-wrap">
                <button
                  onClick={() => handleReorderFrame(0)}
                  disabled={reorderModal.currentIndex === 0}
                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Move to First
                </button>
                <button
                  onClick={() => handleReorderFrame(reorderModal.totalFrames - 1)}
                  disabled={reorderModal.currentIndex === reorderModal.totalFrames - 1}
                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Move to Last
                </button>
                {reorderModal.currentIndex > 0 && (
                  <button
                    onClick={() => handleReorderFrame(reorderModal.currentIndex - 1)}
                    className="px-3 py-1 bg-green-100 text-green-700 rounded text-sm hover:bg-green-200"
                  >
                    Move Up
                  </button>
                )}
                {reorderModal.currentIndex < reorderModal.totalFrames - 1 && (
                  <button
                    onClick={() => handleReorderFrame(reorderModal.currentIndex + 1)}
                    className="px-3 py-1 bg-green-100 text-green-700 rounded text-sm hover:bg-green-200"
                  >
                    Move Down
                  </button>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setReorderModal({ isOpen: false, frame: null, question: '', currentIndex: 0, totalFrames: 0 })}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const input = document.getElementById('new-position') as HTMLInputElement;
                  const newPosition = parseInt(input.value) - 1; // Convert to 0-based index
                  if (newPosition >= 0 && newPosition < reorderModal.totalFrames && newPosition !== reorderModal.currentIndex) {
                    handleReorderFrame(newPosition);
                  }
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Move Frame
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SubmissionsPage;