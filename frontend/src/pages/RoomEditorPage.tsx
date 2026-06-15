import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import RoomEditor from '../components/RoomEditor';
import RoomEditSidebar from '../components/RoomEditSidebar';
import { useRoomEditor } from '../hooks/useRoomEditor';

export default function RoomEditorPage() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const {
    rooms,
    boqItems,
    selectedRoomId,
    setSelectedRoomId,
    isRecalculating,
    error,
    loadData,
    updateRoom,
    addRoom,
    deleteRoom,
    splitRoom,
    mergeRooms,
    addOpening,
    recalculateBOQ,
  } = useRoomEditor(analysisId || '');

  useEffect(() => {
    if (analysisId) {
      loadData();
    }
  }, [analysisId, loadData]);

  const selectedRoom = rooms.find(r => r.id === selectedRoomId);

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex">
      {/* Main Editor */}
      <div className="flex-1 flex flex-col">
        <div className="bg-white border-b px-4 py-3">
          <h1 className="text-xl font-semibold">Room Editor</h1>
          <p className="text-sm text-gray-500">
            Analysis ID: {analysisId} • {rooms.length} rooms
          </p>
        </div>
        <div className="flex-1">
          <RoomEditor
            rooms={rooms}
            onRoomUpdate={updateRoom}
            onRoomAdd={addRoom}
            onRoomDelete={deleteRoom}
            onRoomSplit={splitRoom}
            onRoomMerge={mergeRooms}
            onOpeningAdd={addOpening}
            onBOQRecalculate={recalculateBOQ}
            analysisVersionId={analysisId || ''}
          />
        </div>
      </div>

      {/* Sidebar */}
      <RoomEditSidebar
        selectedRoom={selectedRoom || null}
        onRoomUpdate={updateRoom}
        onRoomDelete={deleteRoom}
        onRoomSplit={splitRoom}
        onRoomMerge={mergeRooms}
        onOpeningAdd={addOpening}
        onBOQRecalculate={recalculateBOQ}
        boqItems={boqItems}
        isRecalculating={isRecalculating}
      />
    </div>
  );
}
