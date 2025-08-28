import { API_ENDPOINTS } from '@/constants';
import type { SearchResult } from '@/types';

export interface SubmitFrameData {
  video_path: string;
  timestamp: number;
  frame_idx: number;
  answer?: string; // Optional answer field
}

export const submitFrame = async (question: string, frameData: SubmitFrameData, answer?: string): Promise<void> => {
  try {
    const response = await fetch(`${API_ENDPOINTS.SUBMIT_SERVER}/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        answer: answer || undefined, // Only include if provided
        video_path: frameData.video_path,
        timestamp: frameData.timestamp,
        frame_idx: frameData.frame_idx,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log('Frame submitted successfully:', result);
  } catch (error) {
    console.error('Error submitting frame:', error);
    throw error;
  }
};

export const submitCurrentFrame = async (
  videoData: SearchResult,
  currentTime: number,
  fps: number
): Promise<void> => {
  const question = prompt('Enter your question for this frame:');
  
  if (!question || question.trim() === '') {
    return; // User cancelled or entered empty question
  }

  // Optional answer prompt
  const answer = prompt('Enter the answer (optional - press Cancel or leave empty to skip):');

  const frameData: SubmitFrameData = {
    video_path: videoData.video_path,
    timestamp: currentTime,
    frame_idx: Math.floor(currentTime * fps),
    answer: answer && answer.trim() ? answer.trim() : undefined,
  };

  await submitFrame(question.trim(), frameData, answer && answer.trim() ? answer.trim() : undefined);
  alert('Frame submitted successfully!');
};
