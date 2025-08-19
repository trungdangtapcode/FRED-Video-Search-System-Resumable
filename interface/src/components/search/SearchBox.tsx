import React, { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import type { SearchType, SearchState } from '@/types';
import { SEARCH_TYPES, DEFAULT_VALUES } from '@/constants';
import { Search, Loader2 } from 'lucide-react';

interface SearchBoxProps {
  searchType: SearchType;
  searchState: SearchState;
  onSearch: (query: string, topK: number) => void;
  onClear: () => void;
}

export const SearchBox: React.FC<SearchBoxProps> = ({
  searchType,
  searchState,
  onSearch,
  onClear,
}) => {
  const [localQuery, setLocalQuery] = useState(searchState.query);
  const [localTopK, setLocalTopK] = useState(searchState.topK);
  
  const config = SEARCH_TYPES[searchType.toUpperCase() as keyof typeof SEARCH_TYPES];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (localQuery.trim() && !config.disabled) {
      onSearch(localQuery.trim(), localTopK);
    }
  };

  const handleClear = () => {
    setLocalQuery('');
    setLocalTopK(DEFAULT_VALUES.TOP_K);
    onClear();
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-1 pt-2 px-2">
        <CardTitle className="text-xs font-medium flex items-center gap-1">
          <Search className="h-3 w-3" />
          {config.label}
          {config.disabled && (
            <span className="text-[10px] text-muted-foreground bg-muted px-1 py-0.5 rounded">
              Soon
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 px-2 pb-2">
        <form onSubmit={handleSubmit} className="space-y-2">
          <div className="space-y-1">
            <Textarea
              placeholder={config.placeholder}
              value={localQuery}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setLocalQuery(e.target.value)}
              disabled={config.disabled || searchState.isLoading}
              className="w-full text-sm min-h-[100px] resize-none text-xs leading-relaxed"
              rows={5}
            />
            <div className="flex items-center gap-2">
              <label htmlFor={`topk-${searchType}`} className="text-[10px] text-muted-foreground min-w-fit">
                Top K:
              </label>
              <Input
                id={`topk-${searchType}`}
                type="number"
                min="1"
                max={DEFAULT_VALUES.MAX_TOP_K}
                value={localTopK}
                onChange={(e) => setLocalTopK(Number(e.target.value))}
                disabled={config.disabled || searchState.isLoading}
                className="w-14 text-xs h-6"
              />
            </div>
          </div>
          
          <div className="flex gap-1">
            <Button
              type="submit"
              disabled={!localQuery.trim() || config.disabled || searchState.isLoading}
              className="flex-1 h-6 text-xs bg-blue-600 hover:bg-blue-700 text-white"
              size="sm"
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
