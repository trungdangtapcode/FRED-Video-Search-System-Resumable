import React, { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { ZoomIn, ZoomOut, Grid3X3, RotateCcw } from 'lucide-react';

interface TopBarProps {
  framesPerRow: number;
  onFramesPerRowChange: (count: number) => void;
  totalResults: number;
}

export const TopBar: React.FC<TopBarProps> = ({ 
  framesPerRow, 
  onFramesPerRowChange, 
  totalResults 
}) => {
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey) {
        if (event.key === '=' || event.key === '+') {
          event.preventDefault();
          onFramesPerRowChange(Math.max(4, framesPerRow - 1));
        } else if (event.key === '-') {
          event.preventDefault();
          onFramesPerRowChange(Math.min(20, framesPerRow + 1));
        } else if (event.key === '0') {
          event.preventDefault();
          onFramesPerRowChange(10); // Reset to default
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [framesPerRow, onFramesPerRowChange]);

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
            title="Zoom In (Ctrl/Cmd + +)"
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
            title="Zoom Out (Ctrl/Cmd + -)"
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
          title="Reset to Default (Ctrl/Cmd + 0)"
        >
          <RotateCcw className="h-3 w-3 mr-1" />
          Reset
        </Button>
      </div>

      <div className="text-xs text-muted-foreground">
        Shortcuts: Ctrl/Cmd + [+/-/0]
      </div>
    </div>
  );
};
