import React, { useState, useRef, useEffect } from 'react';
import { Stage, Layer, Rect, Text, Transformer, Line } from 'react-konva';
import { KonvaEventObject } from 'konva/lib/Node';
import { 
  Pencil, 
  Trash2, 
  Copy, 
  Scissors, 
  Merge, 
  DoorOpen, 
  Maximize2,
  Save
} from 'lucide-react';

interface Room {
  id: string;
  name: string;
  x: number;
  y: number;
  width: number;
  height: number;
  fill: string;
  roomType: string;
  area: number;
}

interface RoomEditorProps {
  rooms: Room[];
  onRoomUpdate: (room: Room) => void;
  onRoomAdd: (room: Room) => void;
  onRoomDelete: (roomId: string) => void;
  onRoomSplit: (roomId: string, direction: 'horizontal' | 'vertical') => void;
  onRoomMerge: (roomIds: string[]) => void;
  onOpeningAdd: (roomId: string, type: 'door' | 'window') => void;
  onBOQRecalculate: () => void;
  analysisVersionId: string;
}

export default function RoomEditor({
  rooms,
  onRoomUpdate,
  onRoomAdd,
  onRoomDelete,
  onRoomSplit,
  onRoomMerge,
  onOpeningAdd,
  onBOQRecalculate,
  analysisVersionId
}: RoomEditorProps) {
  const [selectedRoomId, setSelectedRoomId] = useState<string | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [newRoomStart, setNewRoomStart] = useState<{ x: number; y: number } | null>(null);
  const [selectedRoomIds, setSelectedRoomIds] = useState<string[]>([]);
  const [scale, setScale] = useState(1);
  const stageRef = useRef<any>(null);
  const transformerRef = useRef<any>(null);

  const selectedRoom = rooms.find(r => r.id === selectedRoomId);

  // Handle room selection
  const handleRoomClick = (e: any, roomId: string) => {
    if (e.evt.shiftKey) {
      // Multi-select for merge
      if (selectedRoomIds.includes(roomId)) {
        setSelectedRoomIds(selectedRoomIds.filter(id => id !== roomId));
      } else {
        setSelectedRoomIds([...selectedRoomIds, roomId]);
      }
    } else {
      setSelectedRoomId(roomId);
      setSelectedRoomIds([roomId]);
    }
  };

  // Handle room drag end
  const handleRoomDragEnd = (e: any, room: Room) => {
    const updatedRoom = {
      ...room,
      x: e.target.x(),
      y: e.target.y()
    };
    onRoomUpdate(updatedRoom);
    onBOQRecalculate();
  };

  // Handle room resize
  const handleRoomResize = (newAttrs: any) => {
    if (selectedRoom) {
      const updatedRoom = {
        ...selectedRoom,
        x: newAttrs.x,
        y: newAttrs.y,
        width: newAttrs.width,
        height: newAttrs.height
      };
      onRoomUpdate(updatedRoom);
      onBOQRecalculate();
    }
  };

  // Handle canvas click for drawing new room
  const handleStageClick = (e: any) => {
    if (isDrawing && newRoomStart) {
      const pos = e.target.getStage()?.getPointerPosition();
      if (pos) {
        const width = pos.x - newRoomStart.x;
        const height = pos.y - newRoomStart.y;
        
        if (Math.abs(width) > 20 && Math.abs(height) > 20) {
          const newRoom: Room = {
            id: `room-${Date.now()}`,
            name: `Room ${rooms.length + 1}`,
            x: width > 0 ? newRoomStart.x : pos.x,
            y: height > 0 ? newRoomStart.y : pos.y,
            width: Math.abs(width),
            height: Math.abs(height),
            fill: '#e0f2fe',
            roomType: 'unknown',
            area: Math.abs(width * height) / 10000 // Rough area calculation
          };
          onRoomAdd(newRoom);
          onBOQRecalculate();
        }
      }
      setIsDrawing(false);
      setNewRoomStart(null);
    }
  };

  // Handle stage mouse down for starting to draw
  const handleStageMouseDown = (e: any) => {
    if (e.target === e.target.getStage()) {
      const pos = e.target.getStage()?.getPointerPosition();
      if (pos) {
        setIsDrawing(true);
        setNewRoomStart(pos);
      }
    }
  };

  // Handle stage mouse move for drawing preview
  const handleStageMouseMove = (e: any) => {
    // Could add preview rectangle here
  };

  // Update transformer when selection changes
  useEffect(() => {
    if (selectedRoomId && transformerRef.current) {
      const selectedNode = stageRef.current?.findOne(`#${selectedRoomId}`);
      if (selectedNode) {
        transformerRef.current.nodes([selectedNode]);
        transformerRef.current.getLayer().batchDraw();
      }
    }
  }, [selectedRoomId]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Delete' && selectedRoomId) {
        onRoomDelete(selectedRoomId);
        setSelectedRoomId(null);
        onBOQRecalculate();
      }
      if (e.key === 'd' && selectedRoomIds.length >= 2) {
        onRoomMerge(selectedRoomIds);
        setSelectedRoomIds([]);
        onBOQRecalculate();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedRoomId, selectedRoomIds]);

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="bg-white border-b px-4 py-2 flex items-center gap-2">
        <button
          onClick={() => setIsDrawing(!isDrawing)}
          className={`p-2 rounded ${isDrawing ? 'bg-blue-500 text-white' : 'bg-gray-100 hover:bg-gray-200'}`}
          title="Draw Room"
        >
          <Pencil size={20} />
        </button>
        <button
          onClick={() => selectedRoomId && onRoomDelete(selectedRoomId)}
          disabled={!selectedRoomId}
          className="p-2 rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
          title="Delete Room"
        >
          <Trash2 size={20} />
        </button>
        <button
          onClick={() => selectedRoomId && onRoomSplit(selectedRoomId, 'horizontal')}
          disabled={!selectedRoomId}
          className="p-2 rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
          title="Split Horizontal"
        >
          <Scissors size={20} />
        </button>
        <button
          onClick={() => selectedRoomIds.length >= 2 && onRoomMerge(selectedRoomIds)}
          disabled={selectedRoomIds.length < 2}
          className="p-2 rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
          title="Merge Rooms (Press D)"
        >
          <Merge size={20} />
        </button>
        <button
          onClick={() => selectedRoomId && onOpeningAdd(selectedRoomId, 'door')}
          disabled={!selectedRoomId}
          className="p-2 rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
          title="Add Door"
        >
          <DoorOpen size={20} />
        </button>
        <div className="flex-1" />
        <button
          onClick={onBOQRecalculate}
          className="p-2 rounded bg-green-500 text-white hover:bg-green-600"
          title="Recalculate BOQ"
        >
          <Save size={20} />
        </button>
      </div>

      {/* Canvas */}
      <div className="flex-1 overflow-auto bg-gray-50">
        <Stage
          width={1200}
          height={800}
          scaleX={scale}
          scaleY={scale}
          ref={stageRef}
          onMouseDown={handleStageMouseDown}
          onMouseMove={handleStageMouseMove}
          onClick={handleStageClick}
        >
          <Layer>
            {/* Grid */}
            {[...Array(20)].map((_, i) => (
              <Line
                key={`grid-h-${i}`}
                points={[0, i * 50, 1200, i * 50]}
                stroke="#e5e7eb"
                strokeWidth={1}
              />
            ))}
            {[...Array(24)].map((_, i) => (
              <Line
                key={`grid-v-${i}`}
                points={[i * 50, 0, i * 50, 800]}
                stroke="#e5e7eb"
                strokeWidth={1}
              />
            ))}

            {/* Rooms */}
            {rooms.map((room) => (
              <Rect
                key={room.id}
                id={room.id}
                x={room.x}
                y={room.y}
                width={room.width}
                height={room.height}
                fill={room.id === selectedRoomId ? '#bfdbfe' : room.fill}
                stroke={room.id === selectedRoomId ? '#3b82f6' : '#94a3b8'}
                strokeWidth={room.id === selectedRoomId ? 2 : 1}
                draggable
                onDragEnd={(e) => handleRoomDragEnd(e, room)}
                onClick={(e) => handleRoomClick(e, room.id)}
                onTap={(e) => handleRoomClick(e, room.id)}
              />
            ))}

            {/* Room Labels */}
            {rooms.map((room) => (
              <Text
                key={`label-${room.id}`}
                x={room.x + room.width / 2}
                y={room.y + room.height / 2}
                text={room.name}
                fontSize={14}
                fill="#1e293b"
                align="center"
                verticalAlign="middle"
                offsetX={room.name.length * 4}
                offsetY={7}
              />
            ))}

            {/* Transformer for selected room */}
            {selectedRoomId && (
              <Transformer
                ref={transformerRef}
                boundBoxFunc={(oldBox, newBox) => {
                  if (newBox.width < 20 || newBox.height < 20) {
                    return oldBox;
                  }
                  return newBox;
                }}
                onTransformEnd={() => {
                  if (transformerRef.current && selectedRoom) {
                    const attrs = transformerRef.current.nodes()[0].getAttrs();
                    handleRoomResize(attrs);
                  }
                }}
              />
            )}

            {/* Drawing preview */}
            {isDrawing && newRoomStart && (
              <Rect
                x={newRoomStart.x}
                y={newRoomStart.y}
                width={0}
                height={0}
                fill="rgba(59, 130, 246, 0.3)"
                stroke="#3b82f6"
                strokeWidth={2}
                dash={[5, 5]}
              />
            )}
          </Layer>
        </Stage>
      </div>

      {/* Room Info Panel */}
      {selectedRoom && (
        <div className="bg-white border-t p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Room Properties</h3>
            <button
              onClick={() => setSelectedRoomId(null)}
              className="text-gray-500 hover:text-gray-700"
            >
              ×
            </button>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={selectedRoom.name}
                onChange={(e) => onRoomUpdate({ ...selectedRoom, name: e.target.value })}
                className="w-full px-3 py-2 border rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Room Type</label>
              <select
                value={selectedRoom.roomType}
                onChange={(e) => onRoomUpdate({ ...selectedRoom, roomType: e.target.value })}
                className="w-full px-3 py-2 border rounded"
              >
                <option value="unknown">Unknown</option>
                <option value="living_room">Living Room</option>
                <option value="bedroom">Bedroom</option>
                <option value="kitchen">Kitchen</option>
                <option value="bathroom">Bathroom</option>
                <option value="dining">Dining Room</option>
                <option value="office">Office</option>
                <option value="garage">Garage</option>
                <option value="storage">Storage</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Width (ft)</label>
              <input
                type="number"
                value={selectedRoom.width.toFixed(2)}
                onChange={(e) => onRoomUpdate({ ...selectedRoom, width: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Height (ft)</label>
              <input
                type="number"
                value={selectedRoom.height.toFixed(2)}
                onChange={(e) => onRoomUpdate({ ...selectedRoom, height: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border rounded"
              />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Area (sq ft)</label>
              <input
                type="text"
                value={(selectedRoom.width * selectedRoom.height / 10000).toFixed(2)}
                disabled
                className="w-full px-3 py-2 border rounded bg-gray-100"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
