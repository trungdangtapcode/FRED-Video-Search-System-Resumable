/**
 * Translation Service
 * Handles communication with the Google Translate server
 */

const TRANSLATE_BASE_URL = 'http://38.29.145.80:5002';

export interface TranslationRequest {
  text: string;
  src?: string;
  dest?: string;
}

export interface TranslationResponse {
  original_text: string;
  translated_text: string;
  src_language: string;
  dest_language: string;
  confidence?: number;
}

export interface LanguageDetectionRequest {
  text: string;
}

export interface LanguageDetectionResponse {
  text: string;
  language: string;
  confidence: number;
}

export class TranslationService {
  /**
   * Translate text from one language to another
   */
  static async translateText(request: TranslationRequest): Promise<TranslationResponse> {
    try {
      const response = await fetch(`${TRANSLATE_BASE_URL}/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Translation failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Translation service error:', error);
      throw error;
    }
  }

  /**
   * Translate Vietnamese text to English (convenience method)
   */
  static async translateVietnameseToEnglish(text: string): Promise<TranslationResponse> {
    try {
      const response = await fetch(`${TRANSLATE_BASE_URL}/translate/vietnamese-to-english`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error(`Translation failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Vietnamese translation service error:', error);
      throw error;
    }
  }

  /**
   * Detect the language of the provided text
   */
  static async detectLanguage(request: LanguageDetectionRequest): Promise<LanguageDetectionResponse> {
    try {
      const response = await fetch(`${TRANSLATE_BASE_URL}/detect-language`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Language detection failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Language detection service error:', error);
      throw error;
    }
  }

  /**
   * Check if the translate server is healthy
   */
  static async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${TRANSLATE_BASE_URL}/health`);
      return response.ok;
    } catch (error) {
      console.error('Translation service health check failed:', error);
      return false;
    }
  }
}
