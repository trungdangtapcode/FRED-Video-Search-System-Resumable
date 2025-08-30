import React, { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Search, Loader2 } from 'lucide-react';
import { DEFAULT_VALUES } from '@/constants';

interface UnifiedSearchState {
  query: string;
  ocr: string;
  asr: string;
  topK: number;
  isLoading: boolean;
  results: any[];
  error: string | null;
}

interface UnifiedSearchBoxProps {
  searchState: UnifiedSearchState;
  onSearch: (query: string, ocr: string, asr: string, topK: number) => void;
  onClear: () => void;
}

export const UnifiedSearchBox: React.FC<UnifiedSearchBoxProps> = ({
  searchState,
  onSearch,
  onClear,
}) => {
  const [localQuery, setLocalQuery] = useState(searchState.query);
  const [localOcr, setLocalOcr] = useState(searchState.ocr);
  const [localAsr, setLocalAsr] = useState(searchState.asr);
  const [localTopK, setLocalTopK] = useState(searchState.topK);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const hasContent = localQuery.trim() || localOcr.trim() || localAsr.trim();
    if (hasContent && !searchState.isLoading) {
      onSearch(localQuery.trim(), localOcr.trim(), localAsr.trim(), localTopK);
    }
  };

  const handleClear = () => {
    setLocalQuery('');
    setLocalOcr('');
    setLocalAsr('');
    setLocalTopK(DEFAULT_VALUES.TOP_K);
    onClear();
  };

  // Handle Ctrl+Enter keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.key === 'Enter') {
        event.preventDefault();
        const hasContent = localQuery.trim() || localOcr.trim() || localAsr.trim();
        if (hasContent && !searchState.isLoading) {
          onSearch(localQuery.trim(), localOcr.trim(), localAsr.trim(), localTopK);
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [localQuery, localOcr, localAsr, localTopK, searchState.isLoading, onSearch]);

  const hasContent = localQuery.trim() || localOcr.trim() || localAsr.trim();

  return (
    <Card className="w-full">
      <CardHeader className="pb-1 pt-2 px-2">
        <CardTitle className="text-xs font-medium flex items-center gap-1">
          <Search className="h-3 w-3" />
          Multi-Modal Search
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 px-2 pb-2">
        <form onSubmit={handleSubmit} className="space-y-2">
          {/* Text Query */}
          <div className="space-y-1">
            <label htmlFor="query" className="text-[10px] text-muted-foreground">
              Text Query (optional)
            </label>
            <Textarea
              id="query"
              placeholder="Enter text description..."
              value={localQuery}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setLocalQuery(e.target.value)}
              disabled={searchState.isLoading}
              className="w-full text-sm min-h-[60px] resize-none text-xs leading-relaxed"
              rows={3}

              autoComplete="on"
              spellCheck={true}
            />
          </div>

          {/* OCR Text */}
          <div className="space-y-1">
            <label htmlFor="ocr" className="text-[10px] text-muted-foreground">
              OCR Text (optional)
            </label>
            <Textarea
              id="ocr"
              placeholder="Search by text in images..."
              value={localOcr}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setLocalOcr(e.target.value)}
              disabled={searchState.isLoading}
              className="w-full text-sm min-h-[60px] resize-none text-xs leading-relaxed"
              rows={3}

              autoComplete="on"
              spellCheck={true}
            />
          </div>

          {/* ASR Text */}
          <div className="space-y-1">
            <label htmlFor="asr" className="text-[10px] text-muted-foreground">
              ASR Text (optional)
            </label>
            <Textarea
              id="asr"
              placeholder="Search by speech content..."
              value={localAsr}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setLocalAsr(e.target.value)}
              disabled={searchState.isLoading}
              className="w-full text-sm min-h-[60px] resize-none text-xs leading-relaxed"
              rows={3}

              autoComplete="on"
              spellCheck={true}
            />
          </div>

          {/* Top K */}
          <div className="flex items-center gap-2">
            <label htmlFor="topk" className="text-[10px] text-muted-foreground min-w-fit">
              Top K:
            </label>
            <Input
              id="topk"
              type="number"
              min="1"
              max={DEFAULT_VALUES.MAX_TOP_K}
              value={localTopK}
              onChange={(e) => setLocalTopK(Number(e.target.value))}
              disabled={searchState.isLoading}
              className="w-20 text-sm h-8 px-2"
            />
          </div>
          
          {/* Buttons */}
          <div className="flex gap-1">
            <Button
              type="submit"
              disabled={!hasContent || searchState.isLoading}
              className="flex-1 h-6 text-xs bg-blue-600 hover:bg-blue-700 text-white"
              size="sm"
              title="Search (Ctrl+Enter)"
            >
              {searchState.isLoading ? (
                <>
                  <Loader2 className="h-3 w-3 animate-spin mr-1" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="h-3 w-3 mr-1" />
                  Search
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={handleClear}
              disabled={searchState.isLoading}
              className="h-6 text-xs px-2 text-gray-700 border-gray-300 hover:bg-gray-50"
              size="sm"
            >
              Clear
            </Button>
          </div>
        </form>

        {searchState.error && (
          <div className="text-[10px] text-destructive bg-destructive/10 p-1 rounded">
            {searchState.error}
          </div>
        )}
        
        {searchState.results.length > 0 && (
          <div className="text-[10px] text-muted-foreground">
            Found {searchState.results.length} results
          </div>
        )}
      </CardContent>
    </Card>
  );
};
