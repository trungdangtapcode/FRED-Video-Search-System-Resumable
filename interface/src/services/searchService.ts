import { SearchRequest, SearchResponse } from '@/types';
import { API_ENDPOINTS } from '@/constants';

export class SearchService {
  static async searchByText(request: SearchRequest): Promise<SearchResponse> {
    try {
      const response = await fetch(API_ENDPOINTS.SEARCH, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: SearchResponse = await response.json();
      return data;
    } catch (error) {
      console.error('Search API error:', error);
      throw new Error(error instanceof Error ? error.message : 'Failed to search');
    }
  }

  static getImageUrl(framePath: string): string {
    // Convert the local path to the static server URL
    // Remove the /home/root prefix and add the static server base URL
    const relativePath = framePath.replace('/home/root/', '');
    return `${API_ENDPOINTS.STATIC_SERVER}/${relativePath}`;
  }

  static formatTimestamp(timestamp: number): string {
    const minutes = Math.floor(timestamp / 60);
    const seconds = Math.floor(timestamp % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }
}
