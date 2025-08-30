import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Upload, X, Search } from 'lucide-react';

interface ImageSearchBoxProps {
  onSearch: (imageFile: File, topK: number) => void;
  onClear: () => void;
  isLoading?: boolean;
}

export const ImageSearchBox: React.FC<ImageSearchBoxProps> = ({
  onSearch,
  onClear,
  isLoading = false
}) => {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [topK, setTopK] = useState(5);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        alert('Please select a valid image file (PNG, JPG, JPEG, GIF, BMP, WEBP)');
        return;
      }

      // Validate file size (max 10MB)
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        alert('Image file size must be less than 10MB');
        return;
      }

      setSelectedImage(file);
      
      // Create preview URL
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const handleRemoveImage = () => {
    setSelectedImage(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSearch = () => {
    if (selectedImage) {
      onSearch(selectedImage, topK);
    }
  };

  const handleClear = () => {
    handleRemoveImage();
    onClear();
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      // Directly call our image select logic with the file
      const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        alert('Please select a valid image file (PNG, JPG, JPEG, GIF, BMP, WEBP)');
        return;
      }

      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        alert('Image file size must be less than 10MB');
        return;
      }

      setSelectedImage(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  return (
    <div className="space-y-4">
      {/* Image Upload Area */}
      <div className="space-y-2">
        <div className="text-sm font-medium">Upload Image</div>
        
        {!selectedImage ? (
          <div
            className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-6 text-center cursor-pointer hover:border-muted-foreground/50 transition-colors"
            onClick={() => fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
          >
            <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
            <p className="text-sm text-muted-foreground mb-1">
              Click to upload or drag and drop
            </p>
            <p className="text-xs text-muted-foreground">
              PNG, JPG, GIF, BMP, WEBP (max 10MB)
            </p>
          </div>
        ) : (
          <div className="relative border rounded-lg p-2 bg-muted/50">
            <div className="flex items-center gap-3">
              {previewUrl && (
                <img
                  src={previewUrl}
                  alt="Preview"
                  className="w-16 h-16 object-cover rounded border"
                />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{selectedImage.name}</p>
                <p className="text-xs text-muted-foreground">
                  {(selectedImage.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={handleRemoveImage}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
        
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleImageSelect}
        />
      </div>

      {/* Top K Input */}
      <div className="space-y-2">
        <div className="text-sm font-medium">
          Number of Results
        </div>
        <Input
          id="topK"
          type="number"
          min="1"
          max="100"
          value={topK}
          onChange={(e) => setTopK(Math.max(1, Math.min(100, parseInt(e.target.value) || 5)))}
          className="h-9"
        />
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        <Button
          onClick={handleSearch}
          disabled={!selectedImage || isLoading}
          className="flex-1"
          title="Search similar images"
        >
          {isLoading ? (
            <>
              <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
              Searching...
            </>
          ) : (
            <>
              <Search className="h-4 w-4 mr-2" />
              Search
            </>
          )}
        </Button>
        <Button
          variant="outline"
          onClick={handleClear}
          disabled={isLoading}
          className="px-3"
          title="Clear search"
        >
          Clear
        </Button>
      </div>
    </div>
  );
};
