const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1';

export interface Room {
  id: string;
  name: string;
  room_type?: string;
  width_ft?: number;
  height_ft?: number;
  width_m?: number;
  height_m?: number;
  area_sqft?: number;
  area_sqm?: number;
  polygon_coordinates?: number[][];
}

export interface BOQItem {
  category: string;
  description: string;
  unit: string;
  quantity: number;
  rate: number;
  amount: number;
}

export interface RoomUpdateResponse {
  room: Room;
  boq: {
    boq_items: BOQItem[];
    total_amount?: number;
  };
}

// Get auth token
const getAuthToken = () => {
  return localStorage.getItem('auth_token') || '';
};

// Update room
export async function updateRoom(roomId: string, updates: Partial<Room>): Promise<RoomUpdateResponse> {
  const response = await fetch(`${API_BASE}/room-editor/rooms/${roomId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`,
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw new Error('Failed to update room');
  }

  return response.json();
}

// Create new room
export async function createRoom(analysisVersionId: string, room: Partial<Room>): Promise<RoomUpdateResponse> {
  const response = await fetch(`${API_BASE}/room-editor/rooms`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`,
    },
    body: JSON.stringify({
      analysis_version_id: analysisVersionId,
      ...room,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to create room');
  }

  return response.json();
}

// Delete room
export async function deleteRoom(roomId: string): Promise<{ success: boolean; boq: any }> {
  const response = await fetch(`${API_BASE}/room-editor/rooms/${roomId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to delete room');
  }

  return response.json();
}

// Split room
export async function splitRoom(roomId: string, direction: 'horizontal' | 'vertical', ratio: number = 0.5): Promise<any> {
  const response = await fetch(`${API_BASE}/room-editor/rooms/split`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`,
    },
    body: JSON.stringify({
      room_id: roomId,
      split_direction: direction,
      split_ratio: ratio,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to split room');
  }

  return response.json();
}

// Merge rooms
export async function mergeRooms(roomIds: string[], newName?: string, newRoomType?: string): Promise<any> {
  const response = await fetch(`${API_BASE}/room-editor/rooms/merge`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`,
    },
    body: JSON.stringify({
      room_ids: roomIds,
      new_name: newName,
      new_room_type: newRoomType,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to merge rooms');
  }

  return response.json();
}

// Add opening (door/window)
export async function addOpening(
  roomId: string,
  openingType: 'door' | 'window',
  opening: {
    width_ft?: number;
    height_ft?: number;
    width_m?: number;
    height_m?: number;
    position_x?: number;
    position_y?: number;
  }
): Promise<any> {
  const response = await fetch(`${API_BASE}/room-editor/rooms/${roomId}/openings`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`,
    },
    body: JSON.stringify({
      room_id: roomId,
      opening_type: openingType,
      ...opening,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to add opening');
  }

  return response.json();
}

// Get rooms for analysis version
export async function getRooms(analysisVersionId: string): Promise<Room[]> {
  const response = await fetch(`${API_BASE}/analysis/${analysisVersionId}/rooms`, {
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch rooms');
  }

  const data = await response.json();
  return data.rooms || [];
}

// Get BOQ for analysis version
export async function getBOQ(analysisVersionId: string): Promise<{ boq_items: BOQItem[] }> {
  const response = await fetch(`${API_BASE}/analysis/${analysisVersionId}/boq`, {
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch BOQ');
  }

  return response.json();
}
