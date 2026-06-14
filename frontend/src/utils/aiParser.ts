/**
 * Defensive AI Response Parser
 * 
 * This module provides robust parsing and validation of AI responses for blueprint analysis.
 * It handles malformed JSON, applies defaults, validates room types, and ensures data integrity.
 */

// Allowed room types matching backend configuration
const ALLOWED_ROOM_TYPES = [
  "bedroom", "bathroom", "kitchen", "living_room", "dining_room",
  "corridor", "balcony", "store", "utility", "parking", "lobby",
  "office", "staircase", "lift", "terrace", "unknown"
];

export interface Room {
  name: string;
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  area_px: number;
  area_ft: number;
  confidence: number;
  notes?: string;
  floor?: number;
}

export interface AnalysisResult {
  rooms: Room[];
  total_area_px: number;
  drawing_type: string;
  scale_detected?: string;
  notes: string;
  filename: string;
  provider?: string;
  error_code?: string;
  error_message?: string;
}

/**
 * Strip markdown wrappers from AI response
 */
function stripMarkdownWrappers(responseText: string): string {
  let text = responseText.trim();
  
  if (text.startsWith("```json")) {
    text = text.slice(7);
  }
  if (text.startsWith("```")) {
    text = text.slice(3);
  }
  if (text.endsWith("```")) {
    text = text.slice(0, -3);
  }
  
  return text.trim();
}

/**
 * Attempt to recover malformed JSON
 */
function recoverMalformedJSON(responseText: string): any {
  // Try to extract JSON from text
  const jsonMatch = responseText.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    try {
      return JSON.parse(jsonMatch[0]);
    } catch (e) {
      // Try to fix common JSON issues
      let fixedJson = responseText;
      // Fix trailing commas
      fixedJson = fixedJson.replace(/,\s*}/g, '}');
      fixedJson = fixedJson.replace(/,\s*]/g, ']');
      // Fix unquoted keys (basic attempt)
      fixedJson = fixedJson.replace(/(\w+):/g, '"$1":');
      
      try {
        return JSON.parse(fixedJson);
      } catch (e2) {
        throw new Error(`Failed to parse JSON even after recovery: ${e2}`);
      }
    }
  }
  
  throw new Error("No valid JSON found in response");
}

/**
 * Clamp confidence values to 0-1 range
 */
function clampConfidence(value: number): number {
  return Math.max(0.0, Math.min(1.0, value));
}

/**
 * Validate and normalize room type
 */
function validateRoomType(roomType: string): string {
  const normalized = roomType.toLowerCase();
  return ALLOWED_ROOM_TYPES.includes(normalized) ? normalized : "unknown";
}

/**
 * Apply defaults to missing room fields
 */
function applyRoomDefaults(room: any): Room {
  return {
    name: room.name || room.type || "Unknown",
    type: validateRoomType(room.type || "unknown"),
    x: room.x ?? 0,
    y: room.y ?? 0,
    width: room.width ?? 0,
    height: room.height ?? 0,
    area_px: room.area_px ?? 0,
    area_ft: room.area_ft ?? 0,
    confidence: clampConfidence(room.confidence ?? 0.5),
    notes: room.notes,
    floor: room.floor
  };
}

/**
 * Validate response schema and apply corrections
 */
function validateResponseSchema(data: any, filename: string): AnalysisResult {
  // Ensure rooms array exists
  if (!data.rooms || !Array.isArray(data.rooms)) {
    console.warn("Missing or invalid 'rooms' field, using empty array");
    data.rooms = [];
  }
  
  // Apply defaults and validation to each room
  const validatedRooms = data.rooms
    .filter((room: any) => typeof room === 'object' && room !== null)
    .map(applyRoomDefaults);
  
  // Calculate total area if missing
  if (typeof data.total_area_px !== 'number') {
    data.total_area_px = validatedRooms.reduce((sum: number, room: Room) => sum + room.area_px, 0);
  }
  
  return {
    rooms: validatedRooms,
    total_area_px: data.total_area_px,
    drawing_type: data.drawing_type || "unknown",
    scale_detected: data.scale_detected,
    notes: data.notes || "",
    filename: filename,
    provider: data.provider,
    error_code: data.error_code,
    error_message: data.error_message
  };
}

/**
 * Parse AI response with defensive parsing
 */
export function parseAIResponse(responseText: string, filename: string): AnalysisResult {
  try {
    console.log(`Parsing AI response for ${filename}, length: ${responseText.length}`);
    
    // Strip markdown wrappers
    const strippedText = stripMarkdownWrappers(responseText);
    
    // Try to parse JSON directly
    let data: any;
    try {
      data = JSON.parse(strippedText);
      console.log("Successfully parsed JSON directly");
    } catch (e) {
      console.warn("Direct JSON parse failed, attempting recovery");
      data = recoverMalformedJSON(strippedText);
      console.log("Successfully recovered JSON");
    }
    
    // Validate schema and apply corrections
    const result = validateResponseSchema(data, filename);
    console.log(`Successfully parsed ${result.rooms.length} rooms with total area ${result.total_area_px} px`);
    
    return result;
    
  } catch (error) {
    console.error(`Failed to parse AI response: ${error}`);
    return {
      error_code: "AI_PARSE_FAILED",
      error_message: `Failed to parse AI response: ${error}`,
      filename: filename,
      rooms: [],
      total_area_px: 0,
      drawing_type: "unknown",
      scale_detected: undefined,
      notes: `Parse error: ${error}`
    };
  }
}

/**
 * Retry mechanism for empty responses
 */
export async function parseWithRetry<T>(
  parseFn: () => T,
  maxRetries: number = 1
): Promise<T> {
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const result = await parseFn();
      
      // Check if result indicates empty response
      if (result && typeof result === 'object' && 'error_code' in result) {
        const typedResult = result as any;
        if (typedResult.error_code === "AI_EMPTY_RESPONSE" && attempt < maxRetries) {
          console.warn(`Empty response detected, retrying (attempt ${attempt + 1}/${maxRetries})`);
          continue;
        }
      }
      
      return result;
    } catch (error) {
      lastError = error as Error;
      if (attempt < maxRetries) {
        console.warn(`Parse attempt ${attempt + 1} failed, retrying: ${error}`);
      }
    }
  }
  
  throw lastError || new Error("All retry attempts failed");
}

/**
 * Main defensive AI parser function
 */
export async function defensiveParseAIResponse(
  responseText: string,
  filename: string,
  retryOnEmpty: boolean = true
): Promise<AnalysisResult> {
  if (retryOnEmpty) {
    return parseWithRetry(() => parseAIResponse(responseText, filename));
  }
  return parseAIResponse(responseText, filename);
}
