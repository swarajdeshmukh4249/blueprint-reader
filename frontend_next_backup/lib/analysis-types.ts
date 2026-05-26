export type RoomData = {
  room: string;
  width: number | null;
  height: number | null;
  area: number;
  unit?: string;
  source: string;
  floor?: string;
  confidence?: number;
};

export type BOQItem = {
  sno: string;
  description: string;
  unit: string;
  qty: number;
  rate: number;
  amount: number;
  category: string;
  notes?: string;
};

export type AnalysisResult = {
  source_type?: string;
  method_used?: string;
  rooms_found?: string[];
  features_found?: string[];
  room_data?: RoomData[];
  total_area?: number;
  materials?: Record<string, number>;
  costs?: Record<string, number>;
  vision_used?: boolean;
  vision_confidence?: number;
  drawing_type?: string;
  floor_count?: number;
  building_type?: string;
  rates_basis?: string;
  cost_per_sqft?: number;
  boq_total?: number;
  boq_error?: string;
  vision_error?: string;
  extraction_quality?: { level?: string; score?: number };
  boq_items?: BOQItem[];
  boq_summary?: Record<string, number>;
  gst_breakdown?: {
    material_subtotal?: number;
    labour_subtotal?: number;
    gst_amount?: number;
    grand_total_with_gst?: number;
    gst_pct?: number;
  };
  wall_thickness?: { external_mm?: number; internal_mm?: number };
  scale_detection?: { scale_ratio?: string; method?: string };
  fusion?: { methods?: string[]; confidence?: number };
  openings?: {
    doors: { room: string; count: number; type: string }[];
    windows: { room: string; count: number }[];
  };
};

export type AnalysisJob = {
  id: string;
  file_name: string;
  file_path: string;
  file_type: string | null;
  status: "queued" | "processing" | "completed" | "failed";
  result: AnalysisResult | null;
  error: string | null;
  created_at: string;
};

export const JOB_COLS =
  "id,file_name,file_path,file_type,status,result,error,created_at,updated_at,user_id,org_id";

export function detectFileType(filename: string): string | null {
  const n = filename.toLowerCase();
  if (n.endsWith(".pdf")) return "pdf";
  if (n.endsWith(".dxf")) return "dxf";
  if (n.endsWith(".dwg")) return "dwg";
  if (n.endsWith(".ifc") || n.endsWith(".ifczip")) return "ifc";
  if (n.endsWith(".png") || n.endsWith(".jpg") || n.endsWith(".jpeg")) return "image";
  return null;
}
