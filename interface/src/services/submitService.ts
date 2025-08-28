import { API_ENDPOINTS } from '@/constants';
import type { SearchResult } from '@/types';

export interface SubmitFrameData {
  video_path: string;
  timestamp: number;
  frame_idx: number;
}

export const submitFrame = async (question: string, frameData: SubmitFrameData): Promise<void> => {
  try {
    const response = await fetch(`${API_ENDPOINTS.SUBMIT_SERVER}/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
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

  const frameData: SubmitFrameData = {
    video_path: videoData.video_path,
    timestamp: currentTime,
    frame_idx: Math.floor(currentTime * fps),
  };

  await submitFrame(question.trim(), frameData);
  alert('Frame submitted successfully!');
};
