"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import { useUser, useOrganization } from "@clerk/nextjs";
import { createBrowserSupabaseClient } from "@/lib/supabase/client";
import { formatMaxUpload, validateUploadSize } from "@/lib/upload-limits";
import { downloadBoqCsv, exportBoqViaApi, recalcBoqItem, type BoqExportRow } from "@/lib/boq-export";
import {
  IconAnalyze,
  IconChat,
  IconDxf,
  IconExport,
  IconGrid,
  IconLayer,
  IconOpen,
  IconRoom,
  Icon3D,
  IconWall,
} from "@/components/cad/CadIcons";

type RoomData = {
  room: string;
  width: number | null;
  height: number | null;
  area: number;
  unit?: string;
  source: string;
  floor?: string;
  wall_type?: string;
  confidence?: number;
};
type BOQItem = {
  sno: string;
  description: string;
  unit: string;
  qty: number;
  rate: number;
  amount: number;
  category: string;
  notes?: string;
};
type AnalysisResult = {
  source_type?: string;
  method_used?: string;
  rooms_found?: string[];
  features_found?: string[];
  room_data?: RoomData[];
  total_area?: number;
  materials?: Record<string, number>;
  costs?: Record<string, number>;
  vision_used?: boolean;
  vision_model?: string;
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
type Job = {
  id: string;
  file_name: string;
  file_path: string;
  file_type: string | null;
  status: "queued" | "processing" | "completed" | "failed";
  result: AnalysisResult | null;
  error: string | null;
  created_at: string;
};

const BUCKET = "blueprints";
const COLS =
  "id,file_name,file_path,file_type,status,result,error,created_at,updated_at,user_id,org_id";
const POLL = 3000;

const LAYERS = [
  { name: "A-WALL-EXT", color: "#e51937" },
  { name: "A-WALL-INT", color: "#ffaa00" },
  { name: "A-DOOR", color: "#00a651" },
  { name: "A-ROOM-LABEL", color: "#00bfff" },
  { name: "A-DIM", color: "#cccccc" },
  { name: "DEFPOINTS", color: "#666666" },
];

const COMING_SOON = [
  { label: "Blueprint Chat", icon: IconChat },
  { label: "Revision Diff", icon: IconGrid },
  { label: "Vastu Checker", icon: IconRoom },
  { label: "3D Walkthrough", icon: Icon3D },
  { label: "Live Material Prices", icon: IconWall },
  { label: "Contractor Bids", icon: IconAnalyze },
];

function storagePath(file: File) {
  const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
  const base = file.name.replace(/\.[^.]+$/, "").replace(/[^a-zA-Z0-9\-_]/g, "-");
  return `uploads/${crypto.randomUUID()}-${base}.${ext}`;
}

function groupByCategory(items: BOQItem[]): Record<string, BOQItem[]> {
  return items.reduce(
    (acc, item) => {
      if (!acc[item.category]) acc[item.category] = [];
      acc[item.category].push(item);
      return acc;
    },
    {} as Record<string, BOQItem[]>,
  );
}

type RibbonTab = "home" | "analyze" | "boq" | "export";

export default function BlueprintAnalyzer({ isOrg = false }: { isOrg?: boolean }) {
  const { user } = useUser();
  const { organization } = useOrganization();
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "boq" | "rooms">("overview");
  const [ribbonTab, setRibbonTab] = useState<RibbonTab>("home");
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [editableBoq, setEditableBoq] = useState<BOQItem[] | null>(null);
  const [exporting, setExporting] = useState<string | null>(null);
  const [commandLog, setCommandLog] = useState<string[]>([
    "Blueprint Reader — Indian BOQ from DXF/IFC",
    "Type OPEN to browse · ANALYZE to run extraction",
  ]);
  const [commandInput, setCommandInput] = useState("");
  const [snapOn, setSnapOn] = useState(true);
  const [orthoOn, setOrthoOn] = useState(true);

  const apiBase = process.env.NEXT_PUBLIC_BLUEPRINT_API_URL ?? "";

  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);
  useEffect(() => () => { if (previewUrl) URL.revokeObjectURL(previewUrl); }, [previewUrl]);

  const fileType = useMemo(() => {
    if (!file) return null;
    const n = file.name.toLowerCase();
    if (n.endsWith(".dxf")) return "dxf";
    if (n.endsWith(".ifc") || n.endsWith(".ifczip")) return "ifc";
    return "unknown";
  }, [file]);

  useEffect(() => {
    if (result?.boq_items?.length) {
      setEditableBoq(result.boq_items.map((i) => ({ ...i })));
    } else {
      setEditableBoq(null);
    }
  }, [result?.boq_items]);

  useEffect(() => {
    if (!job || job.status === "completed" || job.status === "failed") return;
    const sb = createBrowserSupabaseClient();
    const poll = async () => {
      const { data } = await sb.from("analysis_jobs").select(COLS).eq("id", job.id).single();
      if (!data) return;
      const j = data as Job;
      setJob(j);
      if (j.result) {
        setResult(j.result);
        setActiveTab("overview");
        setCommandLog((prev) => [...prev, `Analysis complete — ${j.result?.total_area ?? 0} sq ft`]);
      }
      if (j.status === "failed") {
        setError(j.error ?? "Analysis failed");
        setLoading(false);
        setCommandLog((prev) => [...prev, `ERROR: ${j.error ?? "failed"}`]);
      }
      if (j.status === "completed") setLoading(false);
    };
    void poll();
    const id = setInterval(() => void poll(), POLL);
    return () => clearInterval(id);
  }, [job]);

  const logCommand = useCallback((line: string) => {
    setCommandLog((prev) => [...prev.slice(-8), line]);
  }, []);

  const pickFile = () => document.getElementById("cad-file-input")?.click();

  const handleAnalyze = async () => {
    if (!file || !user) return;
    if (fileType !== "dxf" && fileType !== "ifc") {
      setError("Upload DXF or IFC (Revit/ArchiCAD export).");
      logCommand("Unsupported format — use DXF or IFC");
      return;
    }
    const sizeErr = validateUploadSize(file);
    if (sizeErr) {
      setError(sizeErr);
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    setJob(null);
    logCommand(`ANALYZE ${file.name}…`);
    try {
      const sb = createBrowserSupabaseClient();
      const path = storagePath(file);
      const { error: upErr } = await sb.storage
        .from(BUCKET)
        .upload(path, file, { cacheControl: "3600", upsert: false });
      if (upErr) {
        const msg = upErr.message || "";
        if (/maximum|size|too large/i.test(msg)) {
          throw new Error(
            `${msg} — Supabase Storage global limit → ${formatMaxUpload()}. Run storage_bucket_limits.sql.`,
          );
        }
        throw upErr;
      }
      const { data, error: insErr } = await sb
        .from("analysis_jobs")
        .insert({
          file_name: file.name,
          file_path: path,
          file_type: fileType,
          storage_bucket: BUCKET,
          status: "queued",
          user_id: user.id,
          org_id: organization?.id ?? null,
        })
        .select(COLS)
        .single();
      if (insErr) throw insErr;
      setJob(data as Job);
      logCommand("Job queued — waiting for worker");
    } catch (e) {
      setLoading(false);
      const msg = e instanceof Error ? e.message : "Upload failed";
      setError(msg);
      logCommand(`ERROR: ${msg}`);
    }
  };

  const handleCommand = (e: React.FormEvent) => {
    e.preventDefault();
    const cmd = commandInput.trim().toUpperCase();
    if (!cmd) return;
    setCommandInput("");
    logCommand(`> ${cmd}`);
    if (cmd === "OPEN" || cmd === "NEW") pickFile();
    else if (cmd === "ANALYZE" || cmd === "REGEN") void handleAnalyze();
    else if (cmd.startsWith("EXPORT ")) {
      const fmt = cmd.split(" ")[1]?.toLowerCase() as "csv" | "xlsx" | "pdf";
      if (["csv", "xlsx", "pdf"].includes(fmt)) void handleExport(fmt);
    } else logCommand(`Unknown command: ${cmd}`);
  };

  const toggleSection = (cat: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  };

  const roomData = result?.room_data ?? [];
  const boqItems = editableBoq ?? result?.boq_items ?? [];
  const gst = result?.gst_breakdown;
  const boqSummary = result?.boq_summary ?? result?.costs ?? {};
  const totalAreaDisplay = Math.round((result?.total_area ?? 0) * 100) / 100;
  const boqTotal =
    result?.boq_total && result.boq_total > 0
      ? result.boq_total
      : (result?.costs?.["Total Estimated Cost"] ?? 0);
  const costPerSqft =
    result?.cost_per_sqft ??
    (totalAreaDisplay > 0 && boqTotal > 0 ? Math.round(boqTotal / totalAreaDisplay) : 0);
  const grouped = groupByCategory(boqItems);
  const editedBoqTotal = boqItems.reduce((s, i) => s + (i.amount || 0), 0);

  const updateBoqField = (sno: string, field: "qty" | "rate", raw: string) => {
    const num = parseFloat(raw) || 0;
    setEditableBoq((prev) =>
      (prev ?? []).map((it) =>
        it.sno === sno ? recalcBoqItem({ ...it, [field]: num } as BoqExportRow) : it,
      ),
    );
  };

  const handleExport = async (format: "csv" | "xlsx" | "pdf") => {
    if (!boqItems.length) return;
    setExporting(format);
    logCommand(`EXPORT ${format.toUpperCase()}…`);
    try {
      if (format === "csv" || !apiBase) {
        downloadBoqCsv(boqItems, gst as Record<string, number>, `boq.${format === "csv" ? "csv" : format}`);
      } else {
        await exportBoqViaApi(apiBase, boqItems, format, gst, "Blueprint Reader BOQ");
      }
      logCommand(`Exported ${format.toUpperCase()} successfully`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setExporting(null);
    }
  };

  const jobStatusLabel = job?.status?.toUpperCase() ?? "READY";
  const scaleLabel = result?.scale_detection?.scale_ratio ?? "—";

  return (
    <div className="cad-workbench" style={{ margin: isOrg ? 0 : 0 }}>

      {/* ── Ribbon ── */}
      <div className="cad-ribbon">
        <div className="cad-ribbon-tabs">
          {(
            [
              ["home", "Home"],
              ["analyze", "Analyze"],
              ["boq", "BOQ"],
              ["export", "Export"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              className={`cad-ribbon-tab ${ribbonTab === id ? "active" : ""}`}
              onClick={() => setRibbonTab(id)}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="cad-ribbon-panel">
          {ribbonTab === "home" && (
            <>
              <div className="cad-ribbon-group">
                <div className="cad-ribbon-tools">
                  <button type="button" className="cad-tool-btn" onClick={pickFile} title="Open DXF/IFC">
                    <IconOpen />
                    Open
                  </button>
                  <button
                    type="button"
                    className="cad-tool-btn primary"
                    disabled={!file || loading}
                    onClick={() => void handleAnalyze()}
                    title="Run extraction + BOQ"
                  >
                    {loading ? <span className="cad-spinner" /> : <IconAnalyze />}
                    Analyze
                  </button>
                </div>
                <span className="cad-ribbon-group-label">File</span>
              </div>
              <div className="cad-ribbon-group">
                <div className="cad-ribbon-tools">
                  <button type="button" className="cad-tool-btn" disabled title="PDF — Vision quota">
                    <IconDxf />
                    PDF
                  </button>
                  <button type="button" className="cad-tool-btn" onClick={pickFile}>
                    <IconDxf />
                    DXF
                  </button>
                  <button type="button" className="cad-tool-btn" onClick={pickFile}>
                    <IconLayer />
                    IFC
                  </button>
                </div>
                <span className="cad-ribbon-group-label">Import</span>
              </div>
            </>
          )}

          {ribbonTab === "analyze" && (
            <div className="cad-ribbon-group">
              <div className="cad-ribbon-tools">
                <button type="button" className="cad-tool-btn" disabled>
                  <IconRoom />
                  Rooms
                </button>
                <button type="button" className="cad-tool-btn" disabled>
                  <IconWall />
                  Walls
                </button>
                <button type="button" className="cad-tool-btn" disabled>
                  <IconGrid />
                  Scale
                </button>
                <button
                  type="button"
                  className="cad-tool-btn primary"
                  disabled={!result}
                  onClick={() => setActiveTab("rooms")}
                >
                  <IconAnalyze />
                  Results
                </button>
              </div>
              <span className="cad-ribbon-group-label">Geometry</span>
            </div>
          )}

          {ribbonTab === "boq" && (
            <div className="cad-ribbon-group">
              <div className="cad-ribbon-tools">
                <button
                  type="button"
                  className="cad-tool-btn"
                  disabled={!result}
                  onClick={() => setActiveTab("boq")}
                >
                  <IconRoom />
                  Line Items
                </button>
                <button
                  type="button"
                  className="cad-tool-btn"
                  disabled={!boqItems.length}
                  onClick={() => setExpandedSections(new Set(Object.keys(grouped)))}
                >
                  <IconGrid />
                  Expand All
                </button>
              </div>
              <span className="cad-ribbon-group-label">Quantities</span>
            </div>
          )}

          {ribbonTab === "export" && (
            <div className="cad-ribbon-group">
              <div className="cad-ribbon-tools">
                {(["csv", "xlsx", "pdf"] as const).map((fmt) => (
                  <button
                    key={fmt}
                    type="button"
                    className="cad-tool-btn"
                    disabled={!boqItems.length || !!exporting}
                    onClick={() => void handleExport(fmt)}
                  >
                    {exporting === fmt ? <span className="cad-spinner" /> : <IconExport />}
                    {fmt.toUpperCase()}
                  </button>
                ))}
              </div>
              <span className="cad-ribbon-group-label">Output</span>
            </div>
          )}
        </div>
      </div>

      {/* ── Main area ── */}
      <div className="cad-main">
        {/* Left palette */}
        <aside className="cad-panel-left">
          <div className="cad-panel-header">
            <span>Layers</span>
            <IconLayer size={14} />
          </div>
          <div className="cad-panel-body">
            {LAYERS.map((layer, i) => (
              <div key={layer.name} className={`cad-layer-row ${i === 0 ? "active" : ""}`}>
                <span className="cad-layer-swatch" style={{ background: layer.color }} />
                <span style={{ flex: 1, fontFamily: "var(--font-mono-cad)", fontSize: 11 }}>{layer.name}</span>
              </div>
            ))}
            <div style={{ marginTop: 12, borderTop: "1px solid var(--cad-border)", paddingTop: 8 }}>
              <p style={{ fontSize: 10, color: "var(--cad-text-dim)", marginBottom: 6, textTransform: "uppercase" }}>
                Extensions
              </p>
              {COMING_SOON.map(({ label, icon: Icon }) => (
                <div
                  key={label}
                  className="cad-layer-row"
                  style={{ opacity: 0.55, cursor: "not-allowed" }}
                  title="Coming soon"
                >
                  <Icon size={14} />
                  <span style={{ flex: 1, fontSize: 11 }}>{label}</span>
                  <span className="cad-badge cad-badge-soon">Soon</span>
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* Center */}
        <div className="cad-center">
          <div className="cad-viewport-wrap cad-viewport-grid cad-crosshair">
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                flexDirection: "column",
                padding: 12,
                zIndex: 1,
              }}
            >
              {/* Viewport toolbar */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  marginBottom: 8,
                  flexShrink: 0,
                }}
              >
                <span style={{ fontFamily: "var(--font-mono-cad)", fontSize: 11, color: "var(--cad-text-dim)" }}>
                  [{file?.name ?? "UNTITLED"}] — Model
                </span>
                {fileType && (
                  <span className="cad-badge cad-badge-ok">{fileType.toUpperCase()}</span>
                )}
                {job && (
                  <span
                    className={`cad-badge ${job.status === "failed" ? "cad-badge-warn" : "cad-badge-ok"}`}
                  >
                    {job.status}
                  </span>
                )}
              </div>

              <div style={{ flex: 1, display: "flex", gap: 12, minHeight: 0 }}>
                {/* Drop / file */}
                <div style={{ width: 280, flexShrink: 0, display: "flex", flexDirection: "column", gap: 8 }}>
                  <div
                    className={`cad-drop-zone ${dragOver ? "drag-over" : ""}`}
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={(e) => {
                      e.preventDefault();
                      setDragOver(false);
                      const f = e.dataTransfer.files[0];
                      if (f) {
                        const err = validateUploadSize(f);
                        if (err) { setError(err); return; }
                        setFile(f);
                        setError("");
                        logCommand(`Opened ${f.name}`);
                      }
                    }}
                    onClick={pickFile}
                  >
                    <IconDxf size={32} />
                    <p style={{ marginTop: 8, fontWeight: 600, color: "var(--cad-text-bright)" }}>
                      OPEN DRAWING
                    </p>
                    <p style={{ fontSize: 11, color: "var(--cad-text-dim)", marginTop: 4 }}>
                      DXF · IFC — max {formatMaxUpload()}
                    </p>
                  </div>
                  <input
                    id="cad-file-input"
                    type="file"
                    accept=".dxf,.ifc,.ifczip"
                    style={{ display: "none" }}
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (!f) return;
                      const err = validateUploadSize(f);
                      if (err) { setError(err); setFile(null); return; }
                      setFile(f);
                      setError("");
                      logCommand(`Opened ${f.name}`);
                    }}
                  />
                  {file && (
                    <div
                      style={{
                        padding: 8,
                        background: "var(--cad-bg-panel)",
                        border: "1px solid var(--cad-border)",
                        fontSize: 11,
                        fontFamily: "var(--font-mono-cad)",
                      }}
                    >
                      <div style={{ color: "var(--cad-text-bright)", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {file.name}
                      </div>
                      <div style={{ color: "var(--cad-text-dim)", marginTop: 4 }}>
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </div>
                    </div>
                  )}
                  {error && <div className="cad-alert cad-alert-error">{error}</div>}
                  {job && (job.status === "queued" || job.status === "processing") && (
                    <div style={{ padding: 8, border: "1px solid var(--cad-border)", background: "var(--cad-bg-panel)" }}>
                      <div style={{ height: 4, background: "var(--cad-border)", marginBottom: 6 }}>
                        <div
                          style={{
                            height: "100%",
                            width: job.status === "processing" ? "65%" : "25%",
                            background: "var(--cad-blue)",
                            transition: "width 1s",
                          }}
                        />
                      </div>
                      <span style={{ fontSize: 10, fontFamily: "var(--font-mono-cad)", color: "var(--cad-blue)" }}>
                        {job.status === "processing" ? "Extracting geometry…" : "Queued…"}
                      </span>
                    </div>
                  )}
                </div>

                {/* Preview canvas */}
                <div
                  style={{
                    flex: 1,
                    border: "1px solid var(--cad-border)",
                    background: "rgba(0,0,0,0.4)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    minHeight: 0,
                    position: "relative",
                  }}
                >
                  {!file || !previewUrl ? (
                    <div style={{ textAlign: "center", color: "var(--cad-text-dim)" }}>
                      <p style={{ fontFamily: "var(--font-mono-cad)", fontSize: 12 }}>No drawing loaded</p>
                      <p style={{ fontSize: 11, marginTop: 4 }}>Command: OPEN</p>
                    </div>
                  ) : (
                    <div style={{ textAlign: "center" }}>
                      <IconDxf size={48} />
                      <p style={{ marginTop: 12, fontFamily: "var(--font-mono-cad)", color: "#6cb6ff" }}>
                        {fileType?.toUpperCase()} READY
                      </p>
                      <p style={{ fontSize: 11, color: "var(--cad-text-dim)", marginTop: 6 }}>
                        Run ANALYZE to extract rooms & BOQ
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Results pane */}
          {result && (
            <div className="cad-results-pane">
              <div className="cad-results-tabs">
                {(["overview", "boq", "rooms"] as const).map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    className={`cad-results-tab ${activeTab === tab ? "active" : ""}`}
                    onClick={() => setActiveTab(tab)}
                  >
                    {tab === "boq" ? "Bill of Quantities" : tab === "rooms" ? "Room Schedule" : "Properties"}
                  </button>
                ))}
              </div>

              <div className="cad-results-content">
                {(result.vision_error || result.boq_error || totalAreaDisplay < 100) && (
                  <div className="cad-alert cad-alert-warn" style={{ marginBottom: 10 }}>
                    {result.vision_error || result.boq_error || "Low confidence — verify areas before tender."}
                  </div>
                )}

                {activeTab === "overview" && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <div>
                      <p className="cad-stat-label" style={{ marginBottom: 8 }}>Detected spaces</p>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                        {(result.rooms_found?.length ? result.rooms_found : roomData.map((r) => r.room)).map(
                          (r) => (
                            <span key={r} className="cad-badge cad-badge-ok" style={{ fontSize: 10 }}>
                              {r}
                            </span>
                          ),
                        )}
                      </div>
                      {result.method_used && (
                        <p style={{ marginTop: 10, fontSize: 11, fontFamily: "var(--font-mono-cad)", color: "var(--cad-text-dim)" }}>
                          {result.method_used}
                        </p>
                      )}
                    </div>
                    <div>
                      <p className="cad-stat-label" style={{ marginBottom: 8 }}>Cost by section</p>
                      {Object.entries(boqSummary)
                        .filter(([, v]) => v > 0)
                        .slice(0, 8)
                        .map(([k, v]) => (
                          <div
                            key={k}
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              padding: "4px 0",
                              borderBottom: "1px solid var(--cad-border)",
                              fontSize: 11,
                            }}
                          >
                            <span style={{ color: "var(--cad-text-dim)" }}>{k}</span>
                            <span style={{ fontFamily: "var(--font-mono-cad)", color: "var(--cad-green)" }}>
                              ₹{Number(v).toLocaleString("en-IN")}
                            </span>
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                {activeTab === "boq" && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    {gst && (
                      <div className="cad-stat-grid" style={{ marginBottom: 8 }}>
                        {[
                          ["Material", gst.material_subtotal],
                          ["Labour", gst.labour_subtotal],
                          [`GST ${gst.gst_pct ?? 18}%`, gst.gst_amount],
                          ["Total", gst.grand_total_with_gst],
                        ].map(([label, val]) => (
                          <div key={String(label)} className="cad-stat-box">
                            <div className="cad-stat-label">{label}</div>
                            <div className="cad-stat-value accent">
                              {val != null ? `₹${Number(val).toLocaleString("en-IN")}` : "—"}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    <p style={{ fontSize: 11, color: "var(--cad-text-dim)" }}>
                      {boqItems.length} items · editable · {result.rates_basis}
                    </p>
                    {Object.entries(grouped).map(([category, items]) => {
                      const catTotal = items.reduce((s, i) => s + i.amount, 0);
                      const isOpen = expandedSections.has(category);
                      return (
                        <div key={category}>
                          <button type="button" className="cad-collapse-header" onClick={() => toggleSection(category)}>
                            <span>{category}</span>
                            <span style={{ fontFamily: "var(--font-mono-cad)", color: "#6cb6ff" }}>
                              ₹{catTotal.toLocaleString("en-IN")} {isOpen ? "▼" : "▶"}
                            </span>
                          </button>
                          {isOpen && (
                            <table className="cad-table">
                              <thead>
                                <tr>
                                  {["#", "Description", "Unit", "Qty", "Rate", "Amount"].map((h) => (
                                    <th key={h}>{h}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {items.map((item) => (
                                  <tr key={item.sno}>
                                    <td>{item.sno}</td>
                                    <td style={{ maxWidth: 240 }}>
                                      {item.description}
                                      {item.notes && (
                                        <div style={{ fontSize: 10, color: "var(--cad-text-dim)" }}>{item.notes}</div>
                                      )}
                                    </td>
                                    <td>{item.unit}</td>
                                    <td>
                                      <input
                                        className="cad-input"
                                        type="number"
                                        value={item.qty || ""}
                                        onChange={(e) => updateBoqField(item.sno, "qty", e.target.value)}
                                        style={{ width: 72 }}
                                      />
                                    </td>
                                    <td>
                                      <input
                                        className="cad-input"
                                        type="number"
                                        value={item.rate || ""}
                                        onChange={(e) => updateBoqField(item.sno, "rate", e.target.value)}
                                        style={{ width: 88 }}
                                      />
                                    </td>
                                    <td style={{ color: "var(--cad-green)", fontFamily: "var(--font-mono-cad)" }}>
                                      {item.amount > 0 ? item.amount.toLocaleString("en-IN") : "—"}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                {activeTab === "rooms" && (
                  <table className="cad-table">
                    <thead>
                      <tr>
                        {["Room", "W (ft)", "H (ft)", "Area (sq ft)", "Source"].map((h) => (
                          <th key={h}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {roomData.length > 0 ? (
                        roomData.map((r, i) => (
                          <tr key={i}>
                            <td style={{ fontWeight: 600 }}>{r.room}</td>
                            <td>{r.width ?? "—"}</td>
                            <td>{r.height ?? "—"}</td>
                            <td style={{ color: "#6cb6ff" }}>{r.area}</td>
                            <td style={{ fontSize: 10, color: "var(--cad-text-dim)" }}>{r.source}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={5} style={{ textAlign: "center", padding: 24, color: "var(--cad-text-dim)" }}>
                            No rooms extracted
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right properties */}
        <aside className="cad-panel-right">
          <div className="cad-panel-header">Properties</div>
          <div className="cad-panel-body">
            <div className="cad-stat-grid">
              <div className="cad-stat-box">
                <div className="cad-stat-label">Built-up area</div>
                <div className="cad-stat-value accent">
                  {totalAreaDisplay > 0 ? `${totalAreaDisplay.toLocaleString("en-IN")} sq ft` : "—"}
                </div>
              </div>
              <div className="cad-stat-box">
                <div className="cad-stat-label">Rooms</div>
                <div className="cad-stat-value">{roomData.length || "—"}</div>
              </div>
              <div className="cad-stat-box">
                <div className="cad-stat-label">₹ / sq ft</div>
                <div className="cad-stat-value">
                  {costPerSqft > 0 ? `₹${costPerSqft.toLocaleString("en-IN")}` : "—"}
                </div>
              </div>
              <div className="cad-stat-box">
                <div className="cad-stat-label">BOQ total</div>
                <div className="cad-stat-value accent">
                  {boqTotal > 0
                    ? `₹${((gst?.grand_total_with_gst && !editableBoq ? gst.grand_total_with_gst : editedBoqTotal || boqTotal) as number).toLocaleString("en-IN")}`
                    : "—"}
                </div>
              </div>
            </div>

            {result?.wall_thickness && (
              <div style={{ marginTop: 12 }}>
                <p className="cad-stat-label">Wall thickness</p>
                <p style={{ fontSize: 12, fontFamily: "var(--font-mono-cad)", marginTop: 4 }}>
                  Ext {result.wall_thickness.external_mm}mm · Int {result.wall_thickness.internal_mm}mm
                </p>
              </div>
            )}

            {result?.scale_detection && (
              <div style={{ marginTop: 10 }}>
                <p className="cad-stat-label">Scale</p>
                <p style={{ fontSize: 12, fontFamily: "var(--font-mono-cad)", marginTop: 4 }}>
                  {result.scale_detection.scale_ratio}
                </p>
              </div>
            )}

            {result?.building_type && (
              <div style={{ marginTop: 10 }}>
                <p className="cad-stat-label">Building type</p>
                <p style={{ fontSize: 12, marginTop: 4 }}>{result.building_type}</p>
              </div>
            )}

            {result?.rates_basis && (
              <div style={{ marginTop: 10 }}>
                <p className="cad-stat-label">Rates</p>
                <p style={{ fontSize: 11, color: "var(--cad-text-dim)", marginTop: 4, lineHeight: 1.4 }}>
                  {result.rates_basis}
                </p>
              </div>
            )}

            {result?.fusion && (
              <div style={{ marginTop: 10 }}>
                <p className="cad-stat-label">Fusion confidence</p>
                <p style={{ fontSize: 12, fontFamily: "var(--font-mono-cad)", marginTop: 4 }}>
                  {Math.round((result.fusion.confidence ?? 0) * 100)}%
                </p>
              </div>
            )}

            {!result && (
              <p style={{ marginTop: 16, fontSize: 11, color: "var(--cad-text-dim)", lineHeight: 1.5 }}>
                Open a DXF or IFC drawing and run Analyze to populate properties, BOQ, and room schedule.
              </p>
            )}
          </div>
        </aside>
      </div>

      {/* Command line */}
      <form className="cad-command-line" onSubmit={handleCommand}>
        <span className="cad-command-prompt">Command:</span>
        <input
          className="cad-command-input"
          value={commandInput}
          onChange={(e) => setCommandInput(e.target.value)}
          placeholder="OPEN · ANALYZE · EXPORT CSV"
          spellCheck={false}
        />
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", maxWidth: "50%", overflow: "hidden" }}>
          {commandLog.slice(-1).map((line, i) => (
            <span key={i} style={{ fontSize: 11, color: "var(--cad-text-dim)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {line}
            </span>
          ))}
        </div>
      </form>

      {/* Status bar */}
      <div className="cad-status-bar">
        <div className="cad-status-group">
          <span className="cad-status-item">{jobStatusLabel}</span>
          <span className="cad-status-item">SCALE: {scaleLabel}</span>
          <span
            className="cad-status-item clickable"
            onClick={() => setSnapOn((v) => !v)}
            onKeyDown={() => {}}
            role="button"
            tabIndex={0}
          >
            SNAP: {snapOn ? "ON" : "OFF"}
          </span>
          <span
            className="cad-status-item clickable"
            onClick={() => setOrthoOn((v) => !v)}
            role="button"
            tabIndex={0}
          >
            ORTHO: {orthoOn ? "ON" : "OFF"}
          </span>
        </div>
        <div className="cad-status-group">
          <span className="cad-status-item">X: 0.00 Y: 0.00 Z: 0.00</span>
          <span className="cad-status-item">MODEL</span>
          <span className="cad-status-item">DSR INDIA</span>
        </div>
      </div>
    </div>
  );
}
