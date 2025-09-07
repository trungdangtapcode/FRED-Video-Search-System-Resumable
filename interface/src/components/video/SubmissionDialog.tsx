import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Send, X } from 'lucide-react';
import { submissionService, type SubmissionData } from '@/services/submissionService';
import type { SearchResult } from '@/types';

interface SubmissionDialogProps {
  isOpen: boolean;
  onClose: () => void;
  videoData: SearchResult;
  currentTime?: number;
  fps?: number;
}

export const SubmissionDialog: React.FC<SubmissionDialogProps> = ({
  isOpen,
  onClose,
  videoData,
  currentTime,
  fps = -1
}) => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
  }>({ type: null, message: '' });

  // Use provided currentTime or fallback to videoData timestamp
  const frameTime = currentTime ?? videoData.timestamp;
  const frameIndex = Math.floor(frameTime * fps);

  const handleSubmit = async () => {
    if (fps==-1){
      new Error('FPS is not provided for submission' );
      console.error('FPS is not provided for submission');
    }
    if (!question.trim()) {
      setSubmitStatus({
        type: 'error',
        message: 'Please enter a question'
      });
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus({ type: null, message: '' });

    try {
      const submissionData: SubmissionData = {
        question: question.trim(),
        answer: answer.trim() || undefined, // Only include if not empty
        video_path: videoData.video_path,
        timestamp: frameTime,
        frame_idx: frameIndex
      };

      const response = await submissionService.submitQuestion(submissionData);
      
      setSubmitStatus({
        type: 'success',
        message: `Question submitted successfully! Total frames for this question: ${response.total_frames}`
      });

      // Clear the form after successful submission
      setTimeout(() => {
        setQuestion('');
        setAnswer('');
        onClose();
        setSubmitStatus({ type: null, message: '' });
      }, 2000);

    } catch (error) {
      setSubmitStatus({
        type: 'error',
        message: error instanceof Error ? error.message : 'Failed to submit question'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    setQuestion('');
    setAnswer('');
    setSubmitStatus({ type: null, message: '' });
    onClose();
  };

  // Handle Ctrl+S when dialog is open
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.key === 's' && isOpen) {
        event.preventDefault();
        handleSubmit();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [isOpen, question, isSubmitting]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-96 max-w-[90vw] border border-gray-600">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Submit Question</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCancel}
            className="text-gray-400 hover:text-white"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Frame Info */}
        <div className="bg-gray-700 rounded p-3 mb-4 text-sm text-gray-300">
          <div className="font-mono">
            <div>Video: {videoData.video_path.split('/').pop()}</div>
            <div>Timestamp: {frameTime.toFixed(3)}s</div>
            <div>Frame: {frameIndex}</div>
          </div>
        </div>

        {/* Question Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Question about this frame:
          </label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter your question about this frame..."
            className="w-full h-24 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            disabled={isSubmitting}
          />
        </div>

        {/* Answer Input (Optional) */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Answer (optional):
          </label>
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Enter the answer to your question (optional)..."
            className="w-full h-20 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 resize-none"
            disabled={isSubmitting}
          />
          <p className="text-xs text-gray-400 mt-1">
            For Q&A questions where just the frame isn't enough context
          </p>
        </div>

        {/* Status Message */}
        {submitStatus.type && (
          <div className={`mb-4 p-3 rounded text-sm ${
            submitStatus.type === 'success' 
              ? 'bg-green-700 text-green-100 border border-green-600' 
              : 'bg-red-700 text-red-100 border border-red-600'
          }`}>
            {submitStatus.message}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 justify-end">
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={isSubmitting}
            className="bg-gray-700 border-gray-600 text-white hover:bg-gray-600"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || !question.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2"
            title="Submit (Ctrl+S)"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                Submitting...
              </>
            ) : (
              <>
                <Send className="h-4 w-4" />
                Submit
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};
