"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useUser, useOrganization } from "@clerk/nextjs";
import { createBrowserSupabaseClient } from "@/lib/supabase/client";
import { formatMaxUpload, validateUploadSize } from "@/lib/upload-limits";
import {
  detectFileType,
  JOB_COLS,
  type AnalysisJob,
} from "@/lib/analysis-types";

const BUCKET = "blueprints";
const POLL = 3000;
const ACCEPT = ".dxf,.dwg,.ifc,.ifczip,.pdf,.png,.jpg,.jpeg";

function storagePath(file: File) {
  const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
  const base = file.name.replace(/\.[^.]+$/, "").replace(/[^a-zA-Z0-9\-_]/g, "-");
  return `uploads/${crypto.randomUUID()}-${base}.${ext}`;
}

function statusBadge(status: string) {
  if (status === "completed") return "badge-success";
  if (status === "failed") return "badge-danger";
  if (status === "processing") return "badge-info";
  return "badge-warning";
}

export default function UploadWorkspace({ isOrg }: { isOrg: boolean }) {
  const router = useRouter();
  const { user } = useUser();
  const { organization } = useOrganization();
  const base = isOrg ? "/org" : "";

  const [file, setFile] = useState<File | null>(null);
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [recentJobs, setRecentJobs] = useState<AnalysisJob[]>([]);

  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);
  useEffect(() => () => { if (previewUrl) URL.revokeObjectURL(previewUrl); }, [previewUrl]);

  const fileType = file ? detectFileType(file.name) : null;

  useEffect(() => {
    if (!user) return;
    const sb = createBrowserSupabaseClient();
    const load = async () => {
      let q = sb.from("analysis_jobs").select(JOB_COLS).order("created_at", { ascending: false }).limit(8);
      if (isOrg && organization?.id) {
        q = q.eq("org_id", organization.id);
      } else {
        q = q.eq("user_id", user.id).is("org_id", null);
      }
      const { data } = await q;
      if (data) setRecentJobs(data as AnalysisJob[]);
    };
    void load();
  }, [user, organization?.id, isOrg, job?.status]);

  useEffect(() => {
    if (!job || job.status === "completed" || job.status === "failed") return;
    const sb = createBrowserSupabaseClient();
    const poll = async () => {
      const { data } = await sb.from("analysis_jobs").select(JOB_COLS).eq("id", job.id).single();
      if (!data) return;
      const j = data as AnalysisJob;
      setJob(j);
      if (j.status === "completed") {
        setLoading(false);
        router.push(`${base}/dashboard/analysis/${j.id}`);
      }
      if (j.status === "failed") {
        setLoading(false);
        setError(j.error ?? "Analysis failed");
      }
    };
    void poll();
    const id = setInterval(() => void poll(), POLL);
    return () => clearInterval(id);
  }, [job, router, base]);

  const pickFile = () => document.getElementById("upload-input")?.click();

  const onFile = (f: File) => {
    const err = validateUploadSize(f);
    if (err) { setError(err); setFile(null); return; }
    const ft = detectFileType(f.name);
    if (!ft) {
      setError("Supported: DXF, DWG, IFC, PDF, PNG, JPG");
      return;
    }
    setFile(f);
    setError("");
    setJob(null);
  };

  const handleAnalyze = async () => {
    if (!file || !user || !fileType) return;
    setLoading(true);
    setError("");
    try {
      const sb = createBrowserSupabaseClient();
      const path = storagePath(file);
      const { error: upErr } = await sb.storage.from(BUCKET).upload(path, file, {
        cacheControl: "3600",
        upsert: false,
      });
      if (upErr) throw upErr;

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
        .select(JOB_COLS)
        .single();
      if (insErr) throw insErr;
      setJob(data as AnalysisJob);
    } catch (e) {
      setLoading(false);
      setError(e instanceof Error ? e.message : "Upload failed");
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
      <div>
        <p className="eyebrow">New analysis</p>
        <h2 className="page-title">Upload drawing</h2>
        <p className="page-subtitle">
          CAD formats (DXF, DWG, IFC) give the most accurate room data. PDF and images use OCR + vision when needed.
        </p>
      </div>

      <div className="upload-grid">
        <div className="card card-scientific">
          <div className="card-header">
            <span style={{ fontWeight: 700, fontFamily: "var(--font-display)" }}>Source file</span>
            <span className="badge badge-coral">Max {formatMaxUpload()}</span>
          </div>
          <div className="card-body">
            <div
              className={`dropzone ${dragOver ? "active" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                const f = e.dataTransfer.files[0];
                if (f) onFile(f);
              }}
              onClick={pickFile}
            >
              <div className="dropzone-icon">↑</div>
              <p style={{ fontWeight: 700, marginBottom: 6, fontFamily: "var(--font-display)" }}>
                Drop file or click to browse
              </p>
              <p style={{ fontSize: 12, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                DXF · DWG · IFC · PDF · PNG · JPG
              </p>
            </div>
            <input
              id="upload-input"
              type="file"
              accept={ACCEPT}
              style={{ display: "none" }}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) onFile(f);
              }}
            />

            {file && (
              <div
                style={{
                  marginTop: 16,
                  padding: 12,
                  background: "var(--bg-muted)",
                  borderRadius: 8,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: 12,
                }}
              >
                <div style={{ minWidth: 0 }}>
                  <p style={{ fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis" }}>
                    {file.name}
                  </p>
                  <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    {(file.size / 1024 / 1024).toFixed(2)} MB · {fileType?.toUpperCase()}
                  </p>
                </div>
                <span className="badge badge-info">{fileType}</span>
              </div>
            )}

            {error && <div className="alert alert-error" style={{ marginTop: 16 }}>{error}</div>}

            {job && (
              <div className="alert alert-warning" style={{ marginTop: 16 }}>
                Job {job.id.slice(0, 8)}… — <strong>{job.status}</strong>
                {job.status === "processing" && (
                  <>
                    {" — extracting rooms and BOQ…"}
                    {fileType === "dwg" && (
                      <span style={{ display: "block", marginTop: 6, fontSize: 12 }}>
                        DWG can take 2–7 minutes (convert to DXF, then analyze). If stuck over 10 min, export DXF from CAD and re-upload.
                      </span>
                    )}
                  </>
                )}
              </div>
            )}

            <button
              type="button"
              className="btn btn-primary"
              style={{ width: "100%", marginTop: 16 }}
              disabled={!file || loading}
              onClick={() => void handleAnalyze()}
            >
              {loading ? (
                <>
                  <span className="spinner processing-glow" /> Processing…
                </>
              ) : (
                "Run analysis"
              )}
            </button>
          </div>
        </div>

        <div className="card card-scientific">
          <div className="card-header">
            <span style={{ fontWeight: 700, fontFamily: "var(--font-display)" }}>Preview</span>
            <span className="badge badge-muted" style={{ fontFamily: "var(--font-mono)", fontSize: 10 }}>
              LIVE
            </span>
          </div>
          <div className="card-body" style={{ padding: 12 }}>
            <div className="preview-frame" style={{ minHeight: 280 }}>
              {!file || !previewUrl ? (
                <p style={{ color: "var(--text-muted)", fontSize: 13 }}>No file selected</p>
              ) : fileType === "pdf" ? (
                <iframe
                  src={previewUrl}
                  title="PDF preview"
                  style={{ width: "100%", height: 320, border: "none" }}
                />
              ) : fileType === "image" ? (
                <div style={{ position: "relative", width: "100%", height: 320 }}>
                  <Image src={previewUrl} alt="Preview" fill unoptimized style={{ objectFit: "contain" }} />
                </div>
              ) : (
                <div style={{ textAlign: "center", padding: 24 }}>
                  <p style={{ fontSize: 40, marginBottom: 8 }}>📐</p>
                  <p style={{ fontWeight: 600 }}>{fileType?.toUpperCase()} file</p>
                  <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 8 }}>
                    Preview available after analysis for CAD/BIM formats
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <span style={{ fontWeight: 600 }}>Recent projects</span>
          <a href={`${base}/analyses`} className="btn btn-ghost" style={{ padding: "6px 12px" }}>
            View all →
          </a>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>File</th>
                <th>Date</th>
                <th>Status</th>
                <th>Area</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {recentJobs.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: "center", color: "var(--text-muted)", padding: 32 }}>
                    No analyses yet
                  </td>
                </tr>
              ) : (
                recentJobs.map((j) => (
                  <tr key={j.id}>
                    <td style={{ fontWeight: 500 }}>{j.file_name}</td>
                    <td style={{ color: "var(--text-muted)", fontSize: 12 }}>
                      {new Date(j.created_at).toLocaleDateString("en-IN")}
                    </td>
                    <td>
                      <span className={`badge ${statusBadge(j.status)}`}>{j.status}</span>
                    </td>
                    <td style={{ fontFamily: "var(--font-mono)" }}>
                      {j.result?.total_area
                        ? `${Math.round(j.result.total_area).toLocaleString("en-IN")} sq ft`
                        : "—"}
                    </td>
                    <td>
                      {j.status === "completed" && (
                        <a
                          href={`${base}/dashboard/analysis/${j.id}`}
                          className="btn btn-secondary"
                          style={{ padding: "4px 12px", fontSize: 12 }}
                        >
                          Open report
                        </a>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
