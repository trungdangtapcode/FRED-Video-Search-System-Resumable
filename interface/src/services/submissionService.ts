import { API_ENDPOINTS, ROOT_DIR } from '@/constants';

export interface SubmissionData {
  question: string;
  answer?: string; // Optional answer field
  video_path: string;
  timestamp: number;
  frame_idx: number;
}

export interface SubmissionResponse {
  success: boolean;
  message: string;
  total_frames: number;
}

export interface QuestionSubmission {
  video_path: string;
  timestamp: number;
  frame_idx: number;
  submitted_at: string;
  answer?: string; // Optional answer field
}

export interface QuestionsResponse {
  questions: string[];
  total_questions: number;
}

export interface StatsResponse {
  total_questions: number;
  total_frames: number;
  submissions_file: string;
}

class SubmissionService {
  private baseUrl = API_ENDPOINTS.SUBMIT_SERVER;

  async submitQuestion(data: SubmissionData): Promise<SubmissionResponse> {
    try {
      // Remove ROOT_DIR from video path before sending to backend
      const submissionData = {
        ...data,
        video_path: data.video_path.replace(ROOT_DIR, '')
      };

      const response = await fetch(`${this.baseUrl}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submissionData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to submit question');
      }

      return await response.json();
    } catch (error) {
      console.error('Submission error:', error);
      throw error;
    }
  }

  async getQuestions(): Promise<QuestionsResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/questions`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch questions');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching questions:', error);
      throw error;
    }
  }

  async getQuestionSubmissions(question: string): Promise<{
    question: string;
    frames: QuestionSubmission[];
    total_frames: number;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/submissions/${encodeURIComponent(question)}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch question submissions');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching question submissions:', error);
      throw error;
    }
  }

  async getAllSubmissions(): Promise<Record<string, QuestionSubmission[]>> {
    try {
      const response = await fetch(`${this.baseUrl}/submissions`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch all submissions');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching all submissions:', error);
      throw error;
    }
  }

  async getStats(): Promise<StatsResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/stats`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch stats');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching stats:', error);
      throw error;
    }
  }

  async checkHealth(): Promise<{ status: string; timestamp: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      
      if (!response.ok) {
        throw new Error('Health check failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Health check error:', error);
      throw error;
    }
  }

  async deleteFrame(data: SubmissionData): Promise<{
    success: boolean;
    message: string;
    deleted_count: number;
    remaining_frames: number;
  }> {
    try {
      // Remove ROOT_DIR from video path before sending to backend
      const deleteData = {
        ...data,
        video_path: data.video_path.replace(ROOT_DIR, '')
      };

      const response = await fetch(`${this.baseUrl}/delete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(deleteData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to delete frame');
      }

      return await response.json();
    } catch (error) {
      console.error('Delete error:', error);
      throw error;
    }
  }

  async reorderFrames(question: string, frames: QuestionSubmission[]): Promise<{
    success: boolean;
    message: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/reorder`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          frames
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to reorder frames');
      }

      return await response.json();
    } catch (error) {
      console.error('Reorder error:', error);
      throw error;
    }
  }
}

export const submissionService = new SubmissionService();
