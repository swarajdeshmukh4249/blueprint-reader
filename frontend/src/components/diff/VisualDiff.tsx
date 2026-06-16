import React, { useState } from 'react'
import { Stage, Layer, Rect, Text } from 'react-konva'

interface Room {
  id: string
  name: string
  area_sqft: number
  polygon_coordinates?: number[][]
  x?: number
  y?: number
  width?: number
  height?: number
}

interface VersionDiff {
  version1: { version_number: number; rooms: Room[] }
  version2: { version_number: number; rooms: Room[] }
  changes: {
    added: Room[]
    removed: Room[]
    modified: { old: Room; new: Room }[]
    unchanged: Room[]
  }
  area_difference: number
  summary: string
}

interface VisualDiffProps {
  diff: VersionDiff
  mode: 'side-by-side' | 'overlay' | 'diff-only'
  onModeChange: (mode: 'side-by-side' | 'overlay' | 'diff-only') => void
}

export function VisualDiff({ diff, mode, onModeChange }: VisualDiffProps) {
  const [scale, setScale] = useState(1)
  
  const renderRoom = (room: Room, color: string, opacity: number) => {
    if (!room.polygon_coordinates || room.polygon_coordinates.length === 0) {
      // Fallback to simple rectangle if no polygon
      return (
        <Rect
          key={room.id}
          x={room.x || 0}
          y={room.y || 0}
          width={room.width || 50}
          height={room.height || 50}
          fill={color}
          opacity={opacity}
          stroke="black"
          strokeWidth={1 / scale}
        />
      )
    }
    
    // Calculate bounding box from polygon
    const xs = room.polygon_coordinates.map(c => c[0])
    const ys = room.polygon_coordinates.map(c => c[1])
    const minX = Math.min(...xs)
    const minY = Math.min(...ys)
    const maxX = Math.max(...xs)
    const maxY = Math.max(...ys)
    
    return (
      <Rect
        key={room.id}
        x={minX}
        y={minY}
        width={maxX - minX}
        height={maxY - minY}
        fill={color}
        opacity={opacity}
        stroke="black"
        strokeWidth={1 / scale}
      />
    )
  }
  
  return (
    <div className="space-y-4">
      {/* Mode selector */}
      <div className="flex gap-2">
        <button
          className={`px-4 py-2 rounded ${mode === 'side-by-side' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => onModeChange('side-by-side')}
        >
          Side by Side
        </button>
        <button
          className={`px-4 py-2 rounded ${mode === 'overlay' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => onModeChange('overlay')}
        >
          Overlay
        </button>
        <button
          className={`px-4 py-2 rounded ${mode === 'diff-only' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          onClick={() => onModeChange('diff-only')}
        >
          Diff Only
        </button>
      </div>
      
      {/* Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded p-4">
        <p className="text-blue-900">{diff.summary}</p>
        {diff.area_difference !== 0 && (
          <p className="text-sm text-blue-700 mt-1">
            Area difference: {diff.area_difference > 0 ? '+' : ''}{diff.area_difference.toFixed(2)} sq ft
          </p>
        )}
      </div>
      
      {/* Canvas */}
      {mode === 'side-by-side' && (
        <div className="grid grid-cols-2 gap-4">
          <div className="border rounded p-4">
            <h3 className="font-semibold mb-2">Version {diff.version1.version_number}</h3>
            <Stage width={600} height={400} scale={{ x: scale, y: scale }}>
              <Layer>
                {diff.version1.rooms.map(room => 
                  renderRoom(room, '#3b82f6', 0.5)
                )}
              </Layer>
            </Stage>
          </div>
          <div className="border rounded p-4">
            <h3 className="font-semibold mb-2">Version {diff.version2.version_number}</h3>
            <Stage width={600} height={400} scale={{ x: scale, y: scale }}>
              <Layer>
                {diff.version2.rooms.map(room => 
                  renderRoom(room, '#10b981', 0.5)
                )}
              </Layer>
            </Stage>
          </div>
        </div>
      )}
      
      {mode === 'overlay' && (
        <div className="border rounded p-4">
          <Stage width={600} height={400} scale={{ x: scale, y: scale }}>
            <Layer>
              {diff.changes.removed.map(room => renderRoom(room, '#ef4444', 0.3))}
              {diff.changes.added.map(room => renderRoom(room, '#22c55e', 0.5))}
              {diff.changes.unchanged.map(room => renderRoom(room, '#6b7280', 0.2))}
            </Layer>
          </Stage>
        </div>
      )}
      
      {mode === 'diff-only' && (
        <div className="border rounded p-4">
          <Stage width={600} height={400} scale={{ x: scale, y: scale }}>
            <Layer>
              {diff.changes.added.map(room => renderRoom(room, '#22c55e', 0.7))}
              {diff.changes.removed.map(room => renderRoom(room, '#ef4444', 0.7))}
              {diff.changes.modified.map(({ old, new: newRoom }) => (
                <React.Fragment key={old.id}>
                  {renderRoom(old, '#ef4444', 0.4)}
                  {renderRoom(newRoom, '#f59e0b', 0.4)}
                </React.Fragment>
              ))}
            </Layer>
          </Stage>
        </div>
      )}
      
      {/* Zoom controls */}
      <div className="flex gap-2">
        <button className="px-4 py-2 border rounded" onClick={() => setScale(Math.max(0.5, scale - 0.25))}>
          Zoom Out
        </button>
        <button className="px-4 py-2 border rounded" onClick={() => setScale(1)}>
          Reset
        </button>
        <button className="px-4 py-2 border rounded" onClick={() => setScale(Math.min(3, scale + 0.25))}>
          Zoom In
        </button>
      </div>
      
      {/* Legend */}
      <div className="flex gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded" />
          <span>Added</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500 rounded" />
          <span>Removed</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-yellow-500 rounded" />
          <span>Modified</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-gray-500 rounded" />
          <span>Unchanged</span>
        </div>
      </div>
    </div>
  )
}
