import { API_ENDPOINTS } from '@/constants';

/** Convert metadata paths from any machine into a path relative to data/. */
export const toDataRelativePath = (mediaPath: string): string => {
  const normalized = mediaPath.replace(/\\/g, '/');
  const marker = '/data/';
  const markerIndex = normalized.lastIndexOf(marker);

  let relativePath: string;
  if (markerIndex >= 0) {
    relativePath = normalized.slice(markerIndex + marker.length);
  } else if (normalized.startsWith('data/')) {
    relativePath = normalized.slice('data/'.length);
  } else {
    relativePath = normalized.replace(/^\/+/, '');
  }

  const segments = relativePath.split('/').filter(Boolean);
  if (segments.length === 0 || segments.some(segment => segment === '.' || segment === '..')) {
    throw new Error(`Invalid media path: ${mediaPath}`);
  }
  return segments.join('/');
};

export const getMediaUrl = (mediaPath: string): string => {
  const encodedPath = toDataRelativePath(mediaPath)
    .split('/')
    .map(segment => encodeURIComponent(segment))
    .join('/');
  return `${API_ENDPOINTS.STATIC_SERVER}/${encodedPath}`;
};
