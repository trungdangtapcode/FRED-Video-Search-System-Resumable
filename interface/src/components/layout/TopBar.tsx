import React from 'react';
import { Slider } from '@/components/ui/slider';
import { ZoomIn, ZoomOut, Grid3X3 } from 'lucide-react';

interface TopBarProps {
  framesPerRow: number;
  onFramesPerRowChange: (value: number) => void;
  totalResults: number;
}

export const TopBar: React.FC<TopBarProps> = ({ 
  framesPerRow, 
  onFramesPerRowChange, 
  totalResults 
}) => {
  const handleSliderChange = (values: number[]) => {
    onFramesPerRowChange(values[0]);
  };

  return (
    <div className="h-14 bg-background border-b border-border px-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Grid3X3 className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Grid Size:</span>
        </div>
        
        <div className="flex items-center gap-3 min-w-[200px]">
          <ZoomOut className="h-4 w-4 text-muted-foreground" />
          <Slider
            value={[framesPerRow]}
            onValueChange={handleSliderChange}
            max={20}
            min={4}
            step={1}
            className="flex-1"
          />
          <ZoomIn className="h-4 w-4 text-muted-foreground" />
        </div>
        
        <span className="text-sm text-muted-foreground">
          {framesPerRow} per row
        </span>
      </div>
      
      {totalResults > 0 && (
        <div className="text-sm text-muted-foreground">
          {totalResults} results
        </div>
      )}
    </div>
  );
};