import React from 'react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { ZoomIn, ZoomOut, Grid3X3, Grid, Layers, RotateCcw, FileText } from 'lucide-react';
import type { DisplayMode } from '@/types';

interface TopBarProps {
  framesPerRow: number;
  onFramesPerRowChange: (value: number) => void;
  totalResults: number;
  displayMode: DisplayMode;
  onDisplayModeChange: (mode: DisplayMode) => void;
}

export const TopBar: React.FC<TopBarProps> = ({ 
  framesPerRow, 
  onFramesPerRowChange, 
  totalResults,
  displayMode,
  onDisplayModeChange
}) => {
  const handleSliderChange = (values: number[]) => {
    onFramesPerRowChange(values[0]);
  };

  const handleZoomIn = () => {
    onFramesPerRowChange(Math.max(4, framesPerRow - 1));
  };

  const handleZoomOut = () => {
    onFramesPerRowChange(Math.min(20, framesPerRow + 1));
  };

  const handleReset = () => {
    onFramesPerRowChange(10);
  };

  return (
    <div className="h-14 bg-background border-b border-border px-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <span className="text-sm text-muted-foreground">
          {totalResults > 0 ? `${totalResults} results` : 'No results'}
        </span>
        
        {/* Submissions Link */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => window.open('/submissions', '_blank')}
          className="h-8 px-3"
          title="View Submitted Frames"
        >
          <FileText className="h-3 w-3 mr-1" />
          Submissions
        </Button>
        
        {/* Display Mode Toggle */}
        <div className="flex items-center gap-1 border rounded-md p-1">
          <Button
            variant={displayMode === 'all' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => onDisplayModeChange('all')}
            className="h-7 px-3 text-xs"
          >
            <Grid className="h-3 w-3 mr-1" />
            All Frames
          </Button>
          <Button
            variant={displayMode === 'grouped' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => onDisplayModeChange('grouped')}
            className="h-7 px-3 text-xs"
          >
            <Layers className="h-3 w-3 mr-1" />
            Group by Video
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Grid3X3 className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Grid Size</span>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleZoomIn}
            className="h-8 w-8 p-0"
            title="Zoom In"
          >
            <ZoomIn className="h-3 w-3" />
          </Button>
          
          <div className="flex items-center gap-3 min-w-[200px]">
            <span className="text-xs text-muted-foreground w-4">4</span>
            <Slider
              value={[framesPerRow]}
              onValueChange={handleSliderChange}
              max={20}
              min={4}
              step={1}
              className="flex-1"
            />
            <span className="text-xs text-muted-foreground w-6">20</span>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleZoomOut}
            className="h-8 w-8 p-0"
            title="Zoom Out"
          >
            <ZoomOut className="h-3 w-3" />
          </Button>
        </div>

        <div className="text-sm text-muted-foreground">
          <span className="font-medium">{framesPerRow}</span> per row
        </div>
        
        <Button
          variant="outline"
          size="sm"
          onClick={handleReset}
          className="h-8 px-3"
          title="Reset to Default"
        >
          <RotateCcw className="h-3 w-3 mr-1" />
          Reset
        </Button>
      </div>
    </div>
  );
};