import React, { useState } from "react"
import type { SearchResult } from "@/types"
import { SearchService } from "@/services/searchService"
import { Clock, Film, Hash, MapPin } from "lucide-react"

interface FrameTooltipProps {
  children: React.ReactNode
  frameData: SearchResult
  frameIndex: number
}

export const FrameTooltip: React.FC<FrameTooltipProps> = ({ 
  children, 
  frameData, 
  frameIndex 
}) => {
  const [isVisible, setIsVisible] = useState(false)
  const [position, setPosition] = useState({ x: 0, y: 0 })

  const handleMouseEnter = (e: React.MouseEvent) => {
    setIsVisible(true)
    updatePosition(e)
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    updatePosition(e)
  }

  const handleMouseLeave = () => {
    setIsVisible(false)
  }

  const updatePosition = (e: React.MouseEvent) => {
    setPosition({
      x: e.clientX + 15, // Offset from cursor
      y: e.clientY - 10
    })
  }

  const videoName = frameData.video_path.split('/').pop()?.replace('.mp4', '') || 'Unknown'
  const formattedTime = SearchService.formatTimestamp(frameData.timestamp)
  
  return (
    <>
      <div
        onMouseEnter={handleMouseEnter}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        className="cursor-pointer"
      >
        {children}
      </div>
      
      {isVisible && (
        <div
          className="fixed z-[9999] bg-black/95 text-white text-xs rounded-lg p-3 shadow-xl border border-gray-600 backdrop-blur-sm pointer-events-none max-w-xs"
          style={{
            left: position.x,
            top: position.y,
            transform: 'translateY(-100%)'
          }}
        >
          <div className="space-y-2">
            {/* Header */}
            <div className="font-semibold text-blue-300 flex items-center gap-1">
              <Hash className="h-3 w-3" />
              Frame #{frameIndex + 1}
            </div>
            
            {/* Video Info */}
            <div className="flex items-center gap-1 text-green-300">
              <Film className="h-3 w-3" />
              <span className="font-medium">{videoName}</span>
            </div>
            
            {/* Timestamp */}
            <div className="flex items-center gap-1 text-yellow-300">
              <Clock className="h-3 w-3" />
              <span>{formattedTime} ({frameData.timestamp.toFixed(1)}s)</span>
            </div>
            
            {/* Technical Details */}
            <div className="space-y-1 text-gray-300 text-[10px]">
              <div className="flex justify-between">
                <span>Frame Index:</span>
                <span className="text-white">{frameData.frame_idx}</span>
              </div>
              <div className="flex justify-between">
                <span>FPS:</span>
                <span className="text-white">{frameData.fps.toFixed(1)}</span>
              </div>
            </div>
            
            {/* Path Info */}
            <div className="flex items-start gap-1 text-gray-400 text-[10px]">
              <MapPin className="h-3 w-3 mt-0.5 flex-shrink-0" />
              <span className="break-all">{frameData.frame_path}</span>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
