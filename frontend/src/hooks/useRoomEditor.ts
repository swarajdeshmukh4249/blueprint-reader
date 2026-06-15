import { useState, useCallback } from 'react';
import * as roomEditorAPI from '../api/roomEditor';

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

export function useRoomEditor(analysisVersionId: string) {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [boqItems, setBOQItems] = useState<BOQItem[]>([]);
  const [selectedRoomId, setSelectedRoomId] = useState<string | null>(null);
  const [isRecalculating, setIsRecalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load rooms and BOQ
  const loadData = useCallback(async () => {
    try {
      const [roomsData, boqData] = await Promise.all([
        roomEditorAPI.getRooms(analysisVersionId),
        roomEditorAPI.getBOQ(analysisVersionId),
      ]);
      
      // Convert API room data to editor format
      const editorRooms: Room[] = roomsData.map((room: any) => ({
        id: room.id,
        name: room.name,
        x: room.centroid_x || 0,
        y: room.centroid_y || 0,
        width: room.width_ft || 100,
        height: room.height_ft || 100,
        fill: '#e0f2fe',
        roomType: room.room_type || 'unknown',
        area: room.area_sqft || 0,
      }));
      
      setRooms(editorRooms);
      setBOQItems(boqData.boq_items || []);
      setError(null);
    } catch (err) {
      setError('Failed to load data');
      console.error(err);
    }
  }, [analysisVersionId]);

  // Update room
  const updateRoom = useCallback(async (room: Room) => {
    try {
      setIsRecalculating(true);
      
      const response = await roomEditorAPI.updateRoom(room.id, {
        name: room.name,
        room_type: room.roomType,
        width_ft: room.width,
        height_ft: room.height,
        area_sqft: room.area,
      });
      
      // Update local state
      setRooms(prev => prev.map(r => r.id === room.id ? room : r));
      setBOQItems(response.boq.boq_items || []);
      setError(null);
    } catch (err) {
      setError('Failed to update room');
      console.error(err);
    } finally {
      setIsRecalculating(false);
    }
  }, []);

  // Add room
  const addRoom = useCallback(async (room: Room) => {
    try {
      setIsRecalculating(true);
      
      const response = await roomEditorAPI.createRoom(analysisVersionId, {
        name: room.name,
        room_type: room.roomType,
        width_ft: room.width,
        height_ft: room.height,
        area_sqft: room.area,
      });
      
      setRooms(prev => [...prev, room]);
      setBOQItems(response.boq.boq_items || []);
      setError(null);
    } catch (err) {
      setError('Failed to add room');
      console.error(err);
    } finally {
      setIsRecalculating(false);
    }
  }, [analysisVersionId]);

  // Delete room
  const deleteRoom = useCallback(async (roomId: string) => {
    try {
      setIsRecalculating(true);
      
      const response = await roomEditorAPI.deleteRoom(roomId);
      
      setRooms(prev => prev.filter(r => r.id !== roomId));
      setBOQItems(response.boq.boq_items || []);
      setSelectedRoomId(null);
      setError(null);
    } catch (err) {
      setError('Failed to delete room');
      console.error(err);
    } finally {
      setIsRecalculating(false);
    }
  }, []);

  // Split room
  const splitRoom = useCallback(async (roomId: string, direction: 'horizontal' | 'vertical') => {
    try {
      setIsRecalculating(true);
      
      const response = await roomEditorAPI.splitRoom(roomId, direction);
      
      // Update local state with split rooms
      setRooms(prev => {
        const originalRoom = prev.find(r => r.id === roomId);
        if (!originalRoom) return prev;
        
        const updatedOriginal = {
          ...originalRoom,
          width: direction === 'vertical' ? originalRoom.width * 0.5 : originalRoom.width,
          height: direction === 'horizontal' ? originalRoom.height * 0.5 : originalRoom.height,
          area: (originalRoom.width * originalRoom.height) / 2,
        };
        
        const newRoom: Room = {
          ...originalRoom,
          id: response.new_room.id,
          name: response.new_room.name,
          x: direction === 'vertical' ? originalRoom.x + originalRoom.width * 0.5 : originalRoom.x,
          y: direction === 'horizontal' ? originalRoom.y + originalRoom.height * 0.5 : originalRoom.y,
          width: direction === 'vertical' ? originalRoom.width * 0.5 : originalRoom.width,
          height: direction === 'horizontal' ? originalRoom.height * 0.5 : originalRoom.height,
          area: (originalRoom.width * originalRoom.height) / 2,
        };
        
        return prev
          .map(r => r.id === roomId ? updatedOriginal : r)
          .filter(r => r.id !== roomId)
          .concat([updatedOriginal, newRoom]);
      });
      
      setBOQItems(response.boq.boq_items || []);
      setError(null);
    } catch (err) {
      setError('Failed to split room');
      console.error(err);
    } finally {
      setIsRecalculating(false);
    }
  }, []);

  // Merge rooms
  const mergeRooms = useCallback(async (roomIds: string[]) => {
    try {
      setIsRecalculating(true);
      
      const response = await roomEditorAPI.mergeRooms(roomIds);
      
      // Update local state
      setRooms(prev => {
        const roomsToMerge = prev.filter(r => roomIds.includes(r.id));
        const totalArea = roomsToMerge.reduce((sum, r) => sum + r.area, 0);
        const mergedRoom: Room = {
          id: response.merged_room.id,
          name: response.merged_room.name,
          x: roomsToMerge[0].x,
          y: roomsToMerge[0].y,
          width: roomsToMerge[0].width,
          height: roomsToMerge[0].height,
          fill: '#e0f2fe',
          roomType: roomsToMerge[0].roomType,
          area: totalArea,
        };
        
        return prev
          .filter(r => !roomIds.includes(r.id))
          .concat([mergedRoom]);
      });
      
      setBOQItems(response.boq.boq_items || []);
      setSelectedRoomId(null);
      setError(null);
    } catch (err) {
      setError('Failed to merge rooms');
      console.error(err);
    } finally {
      setIsRecalculating(false);
    }
  }, []);

  // Add opening
  const addOpening = useCallback(async (roomId: string, type: 'door' | 'window') => {
    try {
      setIsRecalculating(true);
      
      const response = await roomEditorAPI.addOpening(roomId, type, {});
      
      setBOQItems(response.boq.boq_items || []);
      setError(null);
    } catch (err) {
      setError('Failed to add opening');
      console.error(err);
    } finally {
      setIsRecalculating(false);
    }
  }, []);

  // Recalculate BOQ
  const recalculateBOQ = useCallback(async () => {
    try {
      setIsRecalculating(true);
      
      const boqData = await roomEditorAPI.getBOQ(analysisVersionId);
      setBOQItems(boqData.boq_items || []);
      setError(null);
    } catch (err) {
      setError('Failed to recalculate BOQ');
      console.error(err);
    } finally {
      setIsRecalculating(false);
    }
  }, [analysisVersionId]);

  return {
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
  };
}
