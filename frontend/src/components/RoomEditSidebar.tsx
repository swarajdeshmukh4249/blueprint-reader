import React, { useState } from 'react';
import { 
  Settings, 
  Type, 
  Ruler, 
  Layers, 
  DoorOpen, 
  Square,
  Trash2,
  Copy,
  Scissors,
  Merge,
  Save,
  RefreshCw
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

interface BOQItem {
  category: string;
  description: string;
  unit: string;
  quantity: number;
  rate: number;
  amount: number;
}

interface RoomEditSidebarProps {
  selectedRoom: Room | null;
  onRoomUpdate: (room: Room) => void;
  onRoomDelete: (roomId: string) => void;
  onRoomSplit: (roomId: string, direction: 'horizontal' | 'vertical') => void;
  onRoomMerge: (roomIds: string[]) => void;
  onOpeningAdd: (roomId: string, type: 'door' | 'window') => void;
  onBOQRecalculate: () => void;
  boqItems: BOQItem[];
  isRecalculating: boolean;
}

export default function RoomEditSidebar({
  selectedRoom,
  onRoomUpdate,
  onRoomDelete,
  onRoomSplit,
  onRoomMerge,
  onOpeningAdd,
  onBOQRecalculate,
  boqItems,
  isRecalculating
}: RoomEditSidebarProps) {
  const [activeTab, setActiveTab] = useState<'properties' | 'boq'>('properties');
  const [localRoom, setLocalRoom] = useState<Room | null>(selectedRoom);

  React.useEffect(() => {
    setLocalRoom(selectedRoom);
  }, [selectedRoom]);

  const handlePropertyChange = (field: keyof Room, value: any) => {
    if (localRoom) {
      const updated = { ...localRoom, [field]: value };
      setLocalRoom(updated);
      onRoomUpdate(updated);
    }
  };

  const calculateTotalBOQ = () => {
    return boqItems.reduce((sum, item) => sum + (item.amount || 0), 0);
  };

  if (!selectedRoom) {
    return (
      <div className="w-80 bg-white border-l flex flex-col">
        <div className="p-4 border-b">
          <h2 className="font-semibold text-lg">Room Editor</h2>
          <p className="text-sm text-gray-500 mt-1">Select a room to edit</p>
        </div>
        <div className="flex-1 flex items-center justify-center text-gray-400">
          <Settings size={48} />
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 bg-white border-l flex flex-col">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-semibold text-lg">Room Editor</h2>
          <button
            onClick={onBOQRecalculate}
            disabled={isRecalculating}
            className="p-2 rounded bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50"
            title="Recalculate BOQ"
          >
            {isRecalculating ? (
              <RefreshCw size={18} className="animate-spin" />
            ) : (
              <Save size={18} />
            )}
          </button>
        </div>
        <p className="text-sm text-gray-500">{selectedRoom.name}</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b">
        <button
          onClick={() => setActiveTab('properties')}
          className={`flex-1 px-4 py-2 text-sm font-medium ${
            activeTab === 'properties'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Properties
        </button>
        <button
          onClick={() => setActiveTab('boq')}
          className={`flex-1 px-4 py-2 text-sm font-medium ${
            activeTab === 'boq'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          BOQ
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'properties' ? (
          <div className="p-4 space-y-4">
            {/* Room Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-2">
                <Type size={16} />
                Room Name
              </label>
              <input
                type="text"
                value={localRoom?.name || ''}
                onChange={(e) => handlePropertyChange('name', e.target.value)}
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Room Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-2">
                <Layers size={16} />
                Room Type
              </label>
              <select
                value={localRoom?.roomType || 'unknown'}
                onChange={(e) => handlePropertyChange('roomType', e.target.value)}
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                <option value="balcony">Balcony</option>
                <option value="hallway">Hallway</option>
              </select>
            </div>

            {/* Dimensions */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-2">
                  <Ruler size={16} />
                  Width (ft)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={localRoom?.width?.toFixed(2) || ''}
                  onChange={(e) => handlePropertyChange('width', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-2">
                  <Ruler size={16} />
                  Height (ft)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={localRoom?.height?.toFixed(2) || ''}
                  onChange={(e) => handlePropertyChange('height', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Area */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Area (sq ft)</label>
              <input
                type="text"
                value={((localRoom?.width || 0) * (localRoom?.height || 0) / 10000).toFixed(2)}
                disabled
                className="w-full px-3 py-2 border rounded bg-gray-100 text-gray-600"
              />
            </div>

            {/* Actions */}
            <div className="pt-4 border-t space-y-2">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Actions</p>
              
              <button
                onClick={() => onRoomSplit(selectedRoom.id, 'horizontal')}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
              >
                <Scissors size={16} />
                Split Horizontal
              </button>
              
              <button
                onClick={() => onRoomSplit(selectedRoom.id, 'vertical')}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
              >
                <Scissors size={16} />
                Split Vertical
              </button>

              <button
                onClick={() => onOpeningAdd(selectedRoom.id, 'door')}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
              >
                <DoorOpen size={16} />
                Add Door
              </button>

              <button
                onClick={() => onOpeningAdd(selectedRoom.id, 'window')}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
              >
                <Square size={16} />
                Add Window
              </button>

              <button
                onClick={() => onRoomDelete(selectedRoom.id)}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded"
              >
                <Trash2 size={16} />
                Delete Room
              </button>
            </div>
          </div>
        ) : (
          <div className="p-4 space-y-4">
            {/* BOQ Summary */}
            <div className="bg-blue-50 p-3 rounded">
              <p className="text-sm font-medium text-blue-900">Total BOQ Amount</p>
              <p className="text-2xl font-bold text-blue-900">
                ₹{calculateTotalBOQ().toLocaleString()}
              </p>
            </div>

            {/* BOQ Items */}
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                BOQ Items ({boqItems.length})
              </p>
              <div className="space-y-2">
                {boqItems.map((item, index) => (
                  <div key={index} className="p-3 bg-gray-50 rounded">
                    <p className="text-sm font-medium text-gray-900">{item.category}</p>
                    <p className="text-xs text-gray-600 mt-1">{item.description}</p>
                    <div className="flex justify-between mt-2 text-xs">
                      <span className="text-gray-500">{item.quantity} {item.unit}</span>
                      <span className="font-medium">₹{item.amount?.toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recalculate Button */}
            <button
              onClick={onBOQRecalculate}
              disabled={isRecalculating}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            >
              {isRecalculating ? (
                <>
                  <RefreshCw size={18} className="animate-spin" />
                  Recalculating...
                </>
              ) : (
                <>
                  <RefreshCw size={18} />
                  Recalculate BOQ
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
