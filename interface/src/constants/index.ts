// API endpoints
export const API_ENDPOINTS = {
  SEARCH: 'http://38.29.145.80:5000/retrieve',
  STATIC_SERVER: 'http://38.29.145.80:8069',
} as const;

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
