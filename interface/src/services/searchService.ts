import type { SearchRequest, SearchResponse, UnifiedSearchRequest } from '@/types';
import { API_ENDPOINTS } from '@/constants';

export class SearchService {
  static async searchByText(request: SearchRequest): Promise<SearchResponse> {
    console.log('Sending search request:', request);
    
    try {
      console.log("Sending request to:", API_ENDPOINTS.SEARCH);
      console.log('Request body:', JSON.stringify(request, null, 2));
      const response = await fetch(API_ENDPOINTS.SEARCH, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      console.log('Search API response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      const data: SearchResponse = await response.json();
      for (const item of data) {
        item.fps = parseFloat(item.fps as unknown as string);
        item.frame_idx = parseInt(item.frame_idx as unknown as string, 10);
      }
      console.log('Search API response data:', data);
      return data;
    } catch (error) {
      console.error('Search API error:', error);
      
      // Check if it's a network error
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        throw new Error('Cannot connect to search server. Please make sure the backend server is running on port 5000.');
      }
      
      throw new Error(error instanceof Error ? error.message : 'Failed to search');
    }
  }

  static async unifiedSearch(request: UnifiedSearchRequest): Promise<SearchResponse> {
    console.log('Sending unified search request:', request);
    
    try {
      console.log("Sending request to:", API_ENDPOINTS.SEARCH);
      console.log('Request body:', JSON.stringify(request, null, 2));
      const response = await fetch(API_ENDPOINTS.SEARCH, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      console.log('Search API response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      const data: SearchResponse = await response.json();
      for (const item of data) {
        item.fps = parseFloat(item.fps as unknown as string);
        item.frame_idx = parseInt(item.frame_idx as unknown as string, 10);
      }
      console.log('Search API response data:', data);
      return data;
    } catch (error) {
      console.error('Search API error:', error);
      
      // Check if it's a network error
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        throw new Error('Cannot connect to search server. Please make sure the backend server is running on port 5000.');
      }
      
      throw new Error(error instanceof Error ? error.message : 'Failed to search');
    }
  }

  static getImageUrl(framePath: string): string {
    // Convert the local path to the static server URL
    // Remove the /home/root prefix and add the static server base URL
    const relativePath = framePath.replace('/root/', '');
    return `${API_ENDPOINTS.STATIC_SERVER}/${relativePath}`;
  }

  static formatTimestamp(timestamp: number): string {
    const minutes = Math.floor(timestamp / 60);
    const seconds = Math.floor(timestamp % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }
}
