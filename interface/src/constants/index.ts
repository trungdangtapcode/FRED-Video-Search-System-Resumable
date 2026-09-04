const mediaBaseUrl = (import.meta.env.VITE_MEDIA_BASE_URL || '/media').replace(/\/+$/, '');

// API endpoints
export const API_ENDPOINTS = {
  SEARCH: '/api/retrieve',
  STATIC_SERVER: mediaBaseUrl,
  SUBMIT_SERVER: '/submit-api',
  TRANSLATE_BASE_URL: 'http://localhost:13023',
  SEARCH_BASE_URL: '/api'
} as const;


export const DIRECTLY_DEFAULT = false;

// Default values
export const DEFAULT_VALUES = {
  TOP_K: 100,
  MAX_TOP_K: 500,
} as const;

// Search types configuration
export const SEARCH_TYPES = {
  TEXT: {
    key: 'text' as const,
    label: 'Text Search',
    placeholder: 'Enter text description...',
    disabled: false,
  },
  OCR: {
    key: 'ocr' as const,
    label: 'OCR Search',
    placeholder: 'Search by text in images...',
    disabled: true,
  },
  ASR: {
    key: 'asr' as const,
    label: 'ASR Search',
    placeholder: 'Search by speech content...',
    disabled: true,
  },
} as const;
