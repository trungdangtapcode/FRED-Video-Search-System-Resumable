export async function extractVideoFrame(
  videoUrl: string,
  timestampSeconds: number = 0
): Promise<string> {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    video.crossOrigin = 'anonymous';
    video.preload = 'metadata';
    video.src = videoUrl;
    video.style.display = 'none';

    // Append temporarily to DOM to ensure it can load
    document.body.appendChild(video);

    video.addEventListener('loadedmetadata', () => {
      if (timestampSeconds > video.duration) {
        video.remove();
        return reject(new Error('Timestamp exceeds video duration.'));
      }
      video.currentTime = timestampSeconds;
    });

    video.addEventListener('seeked', () => {
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        video.remove();
        return reject(new Error('Failed to get canvas context.'));
      }

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataURL = canvas.toDataURL('image/jpeg', 0.8);

      // Clean up
      video.remove();
      canvas.remove();

      resolve(dataURL);
    });

    video.addEventListener('error', () => {
      video.remove();
      reject(new Error('Video failed to load or seek.'));
    });

    // Add timeout to prevent hanging
    setTimeout(() => {
      video.remove();
      reject(new Error('Video frame extraction timeout.'));
    }, 10000); // 10 second timeout
  });
}