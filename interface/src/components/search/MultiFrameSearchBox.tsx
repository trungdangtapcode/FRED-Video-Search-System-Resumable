import React, { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Search, Loader2, Plus, Minus, Clock } from 'lucide-react';
import { DEFAULT_VALUES } from '@/constants';
import { TranslationService } from '@/services/translationService';

interface FrameQuery {
  id: string;
  query: string;
  ocr: string;
  asr: string;
  timestamp: number;
}

interface MultiFrameSearchState {
  frames: FrameQuery[];
  topK: number;
  isLoading: boolean;
  results: any[];
  error: string | null;
}

interface MultiFrameSearchBoxProps {
  searchState: MultiFrameSearchState;
  onSearch: (frames: FrameQuery[], topK: number) => void;
  onClear: () => void;
}

export const MultiFrameSearchBox: React.FC<MultiFrameSearchBoxProps> = ({
  searchState,
  onSearch,
  onClear,
}) => {
  const [localFrames, setLocalFrames] = useState<FrameQuery[]>(searchState.frames);
  const [localTopK, setLocalTopK] = useState(searchState.topK);
  const [translatingFrameId, setTranslatingFrameId] = useState<string | null>(null);

  const addFrame = () => {
    if (localFrames.length < 3) {
      const newFrame: FrameQuery = {
        id: `frame_${Date.now()}`,
        query: '',
        ocr: '',
        asr: '',
        timestamp: 0
      };
      setLocalFrames([...localFrames, newFrame]);
    }
  };

  const removeFrame = (frameId: string) => {
    if (localFrames.length > 1) {
      setLocalFrames(localFrames.filter(frame => frame.id !== frameId));
    }
  };

  const updateFrame = (frameId: string, field: keyof FrameQuery, value: string | number) => {
    setLocalFrames(localFrames.map(frame => 
      frame.id === frameId ? { ...frame, [field]: value } : frame
    ));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const hasContent = localFrames.some(frame => 
      frame.query.trim() || frame.ocr.trim() || frame.asr.trim()
    );
    if (hasContent && !searchState.isLoading) {
      onSearch(localFrames, localTopK);
    }
  };

  const handleClear = () => {
    setLocalFrames([{
      id: 'frame_1',
      query: '',
      ocr: '',
      asr: '',
      timestamp: 0
    }]);
    setLocalTopK(DEFAULT_VALUES.TOP_K);
    onClear();
  };

  // Translation function for a specific frame
  const handleTranslateFrame = async (frameId: string) => {
    const frame = localFrames.find(f => f.id === frameId);
    if (!frame || !frame.query.trim()) {
      console.log('No query text to translate for frame:', frameId);
      return;
    }

    setTranslatingFrameId(frameId);
    try {
      const result = await TranslationService.translateVietnameseToEnglish(frame.query);
      updateFrame(frameId, 'query', result.translated_text);
      console.log('Translation successful for frame:', frameId, result);
    } catch (error) {
      console.error('Translation failed for frame:', frameId, error);
      // Optionally show error to user
    } finally {
      setTranslatingFrameId(null);
    }
  };

  // Handle Ctrl+Enter keyboard shortcut and Ctrl+Shift+T for translation
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.key === 'Enter') {
        event.preventDefault();
        const hasContent = localFrames.some(frame => 
          frame.query.trim() || frame.ocr.trim() || frame.asr.trim()
        );
        if (hasContent && !searchState.isLoading) {
          onSearch(localFrames, localTopK);
        }
      }
      
      if (event.ctrlKey && event.key === 'Q') {
        event.preventDefault(); // Prevent browser default action
        // Translate the first frame with content
        const frameWithQuery = localFrames.find(frame => frame.query.trim());
        if (frameWithQuery) {
          handleTranslateFrame(frameWithQuery.id);
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [localFrames, localTopK, searchState.isLoading, onSearch]);

  const hasContent = localFrames.some(frame => 
    frame.query.trim() || frame.ocr.trim() || frame.asr.trim()
  );

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-medium flex items-center gap-2">
          <Search className="h-4 w-4" />
          Multi-Frame Search
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Describe 2-3 frames from the same video with their approximate timestamps
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Frame Inputs */}
          {localFrames.map((frame, index) => (
            <div key={frame.id} className="space-y-3 p-3 border rounded-lg bg-muted/20">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium">Frame {index + 1}</h4>
                <div className="flex items-center gap-2">
                  {localFrames.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFrame(frame.id)}
                      disabled={searchState.isLoading}
                    >
                      <Minus className="h-3 w-3" />
                    </Button>
                  )}
                  {index === localFrames.length - 1 && localFrames.length < 3 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={addFrame}
                      disabled={searchState.isLoading}
                    >
                      <Plus className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              </div>

              {/* Timestamp Input */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  Expected Timestamp (seconds)
                </label>
                <Input
                  type="number"
                  value={frame.timestamp}
                  onChange={(e) => updateFrame(frame.id, 'timestamp', parseFloat(e.target.value) || 0)}
                  placeholder="0"
                  disabled={searchState.isLoading}
                  min="0"
                  step="0.1"
                  className="text-xs"
                />
              </div>

              {/* Text Query */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">
                  Text Description
                </label>
                <Textarea
                  value={frame.query}
                  onChange={(e) => updateFrame(frame.id, 'query', e.target.value)}
                  placeholder="Describe what you see in this frame..."
                  disabled={searchState.isLoading || translatingFrameId === frame.id}
                  rows={2}
                  className="text-xs resize-none"
                />
              </div>

              {/* OCR Input */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">
                  OCR Text (Optional)
                </label>
                <Input
                  value={frame.ocr}
                  onChange={(e) => updateFrame(frame.id, 'ocr', e.target.value)}
                  placeholder="Text visible in the frame..."
                  disabled={searchState.isLoading}
                  className="text-xs"
                />
              </div>

              {/* ASR Input */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">
                  ASR Text (Optional)
                </label>
                <Input
                  value={frame.asr}
                  onChange={(e) => updateFrame(frame.id, 'asr', e.target.value)}
                  placeholder="Speech/audio content..."
                  disabled={searchState.isLoading}
                  className="text-xs"
                />
              </div>
            </div>
          ))}

          {/* Top K Input */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">
              Number of Results
            </label>
            <Input
              type="number"
              value={localTopK}
              onChange={(e) => setLocalTopK(Math.min(DEFAULT_VALUES.MAX_TOP_K, Math.max(1, parseInt(e.target.value) || DEFAULT_VALUES.TOP_K)))}
              min="1"
              max={DEFAULT_VALUES.MAX_TOP_K}
              disabled={searchState.isLoading}
              className="text-xs"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 pt-2">
            <Button
              type="submit"
              disabled={!hasContent || searchState.isLoading}
              className="flex-1 h-8 text-xs min-w-0"
              title="Multi Search (Ctrl+Enter)"
            >
              {searchState.isLoading ? (
                <>
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="mr-1 h-3 w-3" />
                  Multi Search
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={handleClear}
              disabled={searchState.isLoading}
              className="h-8 text-xs px-3"
            >
              Clear
            </Button>
          </div>

          {/* Error Display */}
          {searchState.error && (
            <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded p-2">
              {searchState.error}
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
};
