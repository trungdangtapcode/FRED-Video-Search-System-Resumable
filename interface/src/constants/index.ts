// API endpoints
export const API_ENDPOINTS = {
  SEARCH: 'http://111.237.107.89:50313/retrieve',
  STATIC_SERVER: 'http://103.155.161.181:13021',
  SUBMIT_SERVER: 'http://103.155.161.181:13022',
  // COMPETITION_SUBMIT: 'http://103.155.161.181:13023',
  TRANSLATE_BASE_URL: 'http://103.155.161.181:13023',
  SEARCH_BASE_URL: 'http://111.237.107.89:50313'
} as const;


export const DIRECTLY_DEFAULT = true;

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


export const ROOT_DIR = "/data/root"