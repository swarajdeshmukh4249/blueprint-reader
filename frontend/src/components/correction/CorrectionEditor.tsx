import React, { useState, useRef, useCallback } from 'react'
import { Stage, Layer, Rect, Transformer } from 'react-konva'
import { KonvaEventObject } from 'konva/lib/Node'

interface Room {
  id: string
  name: string
  room_type: string
  area_sqft: number
  width_ft: number
  height_ft: number
  x: number
  y: number
  polygon_coordinates?: number[][]
  confidence_score: number
}

interface CorrectionEditorProps {
  analysisVersionId: string
  rooms: Room[]
  onRoomUpdate: (roomId: string, updates: Partial<Room>) => void
  onRoomAdd: (room: Omit<Room, 'id'>) => void
  onRoomDelete: (roomId: string) => void
}

type Tool = 'select' | 'rename' | 'resize' | 'add' | 'delete' | 'split' | 'merge'

export default function CorrectionEditor({ analysisVersionId, rooms, onRoomUpdate, onRoomAdd, onRoomDelete }: CorrectionEditorProps) {
  const [localRooms, setLocalRooms] = useState(rooms)
  const [selectedId, selectShape] = useState<string | null>(null)
  const [tool, setTool] = useState<Tool>('select')
  const stageRef = useRef<any>(null)
  const transformerRef = useRef<any>(null)
  
  const handleRoomClick = useCallback((e: KonvaEventObject<MouseEvent>, roomId: string) => {
    if (tool === 'select') {
      selectShape(roomId)
    } else if (tool === 'delete') {
      onRoomDelete(roomId)
      setLocalRooms(localRooms.filter(r => r.id !== roomId))
    }
  }, [tool, localRooms, onRoomDelete])
  
  const handleRoomDragEnd = useCallback((e: KonvaEventObject<DragEvent>, roomId: string) => {
    const room = localRooms.find(r => r.id === roomId)
    if (!room) return
    
    const newX = e.target.x()
    const newY = e.target.y()
    
    onRoomUpdate(roomId, {
      x: newX,
      y: newY
    })
  }, [localRooms, onRoomUpdate])
  
  const handleTransformEnd = useCallback((e: KonvaEventObject<Event>, roomId: string) => {
    const room = localRooms.find(r => r.id === roomId)
    if (!room) return
    
    const node = e.target
    const scaleX = node.scaleX()
    const scaleY = node.scaleY()
    
    node.scaleX(1)
    node.scaleY(1)
    
    const newWidth = room.width_ft * scaleX
    const newHeight = room.height_ft * scaleY
    const newArea = newWidth * newHeight
    
    onRoomUpdate(roomId, {
      width_ft: newWidth,
      height_ft: newHeight,
      area_sqft: newArea
    })
  }, [localRooms, onRoomUpdate])
  
  const handleAddRoom = useCallback((e: KonvaEventObject<MouseEvent>) => {
    if (tool !== 'add') return
    
    const stage = stageRef.current
    const pos = stage.getPointerPosition()
    
    const newRoom: Omit<Room, 'id'> = {
      name: 'New Room',
      room_type: 'unknown',
      x: pos.x,
      y: pos.y,
      width_ft: 10,
      height_ft: 10,
      area_sqft: 100,
      confidence_score: 1.0
    }
    
    onRoomAdd(newRoom)
  }, [tool, onRoomAdd])
  
  return (
    <div className="flex h-screen">
      {/* Toolbar */}
      <div className="w-16 border-r bg-gray-50 p-2 flex flex-col gap-2">
        <ToolButton tool="select" currentTool={tool} onClick={setTool} icon="🖱️" />
        <ToolButton tool="rename" currentTool={tool} onClick={setTool} icon="✏️" />
        <ToolButton tool="resize" currentTool={tool} onClick={setTool} icon="📐" />
        <ToolButton tool="add" currentTool={tool} onClick={setTool} icon="➕" />
        <ToolButton tool="delete" currentTool={tool} onClick={setTool} icon="🗑️" />
        <ToolButton tool="split" currentTool={tool} onClick={setTool} icon="✂️" />
        <ToolButton tool="merge" currentTool={tool} onClick={setTool} icon="🔗" />
      </div>
      
      {/* Canvas */}
      <div className="flex-1 bg-gray-100">
        <Stage
          ref={stageRef}
          width={1200}
          height={800}
          onClick={handleAddRoom}
        >
          <Layer>
            {localRooms.map(room => (
              <Rect
                key={room.id}
                x={room.x}
                y={room.y}
                width={room.width_ft * 10} // Scale for display
                height={room.height_ft * 10}
                fill={selectedId === room.id ? '#3b82f6' : '#e5e7eb'}
                stroke={selectedId === room.id ? '#1d4ed8' : '#9ca3af'}
                strokeWidth={2}
                draggable={tool === 'select'}
                onClick={(e) => handleRoomClick(e, room.id)}
                onDragEnd={(e) => handleRoomDragEnd(e, room.id)}
                onTransformEnd={(e) => handleTransformEnd(e, room.id)}
              />
            ))}
            
            {selectedId && (
              <Transformer
                ref={transformerRef}
                boundBoxFunc={(oldBox, newBox) => {
                  if (newBox.width < 20 || newBox.height < 20) return oldBox
                  return newBox
                }}
              />
            )}
          </Layer>
        </Stage>
      </div>
      
      {/* Properties Panel */}
      <div className="w-80 border-l bg-white p-4">
        {selectedId && (() => {
          const room = localRooms.find(r => r.id === selectedId)
          if (!room) return null
          
          return (
            <div className="space-y-4">
              <h3 className="font-semibold">Room Properties</h3>
              
              <div>
                <label className="block text-sm font-medium">Name</label>
                <input
                  type="text"
                  value={room.name}
                  onChange={(e) => onRoomUpdate(room.id, { name: e.target.value })}
                  className="w-full border rounded px-2 py-1"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium">Type</label>
                <select
                  value={room.room_type}
                  onChange={(e) => onRoomUpdate(room.id, { room_type: e.target.value })}
                  className="w-full border rounded px-2 py-1"
                >
                  <option value="bedroom">Bedroom</option>
                  <option value="living_room">Living Room</option>
                  <option value="kitchen">Kitchen</option>
                  <option value="bathroom">Bathroom</option>
                  <option value="balcony">Balcony</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium">Area (sq ft)</label>
                <input
                  type="number"
                  value={room.area_sqft}
                  onChange={(e) => onRoomUpdate(room.id, { area_sqft: parseFloat(e.target.value) })}
                  className="w-full border rounded px-2 py-1"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium">Width (ft)</label>
                <input
                  type="number"
                  value={room.width_ft}
                  onChange={(e) => onRoomUpdate(room.id, { width_ft: parseFloat(e.target.value) })}
                  className="w-full border rounded px-2 py-1"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium">Height (ft)</label>
                <input
                  type="number"
                  value={room.height_ft}
                  onChange={(e) => onRoomUpdate(room.id, { height_ft: parseFloat(e.target.value) })}
                  className="w-full border rounded px-2 py-1"
                />
              </div>
            </div>
          )
        })()}
      </div>
    </div>
  )
}

function ToolButton({ tool, currentTool, onClick, icon }: { tool: Tool, currentTool: Tool, onClick: (t: Tool) => void, icon: string }) {
  return (
    <button
      onClick={() => onClick(tool)}
      className={`p-2 rounded ${currentTool === tool ? 'bg-blue-500 text-white' : 'hover:bg-gray-200'}`}
      title={tool}
    >
      {icon}
    </button>
  )
}
