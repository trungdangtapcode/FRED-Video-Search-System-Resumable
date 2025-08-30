import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { SubmissionDialog } from './SubmissionDialog';
import type { SearchResult } from '@/types';

interface SubmitFrameButtonProps {
  videoData: SearchResult;
  currentTime: number;
  fps: number;
}

export const SubmitFrameButton: React.FC<SubmitFrameButtonProps> = ({
  videoData,
  currentTime,
  fps
}) => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsDialogOpen(true)}
        data-submit-frame-button
        title="Submit current frame with question (Ctrl+S)"
        className="bg-green-700 border-green-600 text-white hover:bg-green-600"
      >
        <Plus className="h-4 w-4" />
        Submit Frame
      </Button>

      <SubmissionDialog
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        videoData={videoData}
        currentTime={currentTime}
        fps={fps}
      />
    </>
  );
};
