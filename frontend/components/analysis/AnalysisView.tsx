"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { downloadBoqCsv, exportBoqViaApi, recalcBoqItem, type BoqExportRow } from "@/lib/boq-export";
import type { AnalysisJob, AnalysisResult, BOQItem } from "@/lib/analysis-types";

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

export default function AnalysisView({
  job,
  basePath,
}: {
  job: AnalysisJob;
  basePath: string;
}) {
  const result = job.result;
  const [activeTab, setActiveTab] = useState<"overview" | "boq" | "rooms">("overview");
  const [editableBoq, setEditableBoq] = useState<BOQItem[] | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [exporting, setExporting] = useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_BLUEPRINT_API_URL ?? "";

  useEffect(() => {
    if (result?.boq_items?.length) {
      setEditableBoq(result.boq_items.map((i) => ({ ...i })));
    }
  }, [result?.boq_items]);

  if (job.status === "failed") {
    return (
      <div className="alert alert-error">
        <strong>Analysis failed</strong>
        <p style={{ marginTop: 8 }}>{job.error}</p>
        <Link href={`${basePath}/dashboard`} className="btn btn-secondary" style={{ marginTop: 16 }}>
          ← New analysis
        </Link>
      </div>
    );
  }

  if (!result || job.status !== "completed") {
    return (
      <div className="card" style={{ padding: 48, textAlign: "center" }}>
        <span className="spinner" style={{ margin: "0 auto 16px", display: "block" }} />
        <p>Loading report…</p>
        <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 8 }}>Status: {job.status}</p>
      </div>
    );
  }

  const roomData = result.room_data ?? [];
  const boqItems = editableBoq ?? result.boq_items ?? [];
  const gst = result.gst_breakdown;
  const boqSummary = result.boq_summary ?? result.costs ?? {};
  const totalArea = Math.round((result.total_area ?? 0) * 100) / 100;
  const boqTotal =
    result.boq_total && result.boq_total > 0
      ? result.boq_total
      : (result.costs?.["Total Estimated Cost"] ?? 0);
  const costPerSqft =
    result.cost_per_sqft ??
    (totalArea > 0 && boqTotal > 0 ? Math.round(boqTotal / totalArea) : 0);
  const grouped = groupByCategory(boqItems);
  const editedTotal = boqItems.reduce((s, i) => s + (i.amount || 0), 0);

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
    try {
      if (format === "csv" || !apiBase) {
        downloadBoqCsv(boqItems, gst as Record<string, number>, `boq-${job.id.slice(0, 8)}.csv`);
      } else {
        await exportBoqViaApi(apiBase, boqItems, format, gst, "Blueprint Reader BOQ");
      }
    } finally {
      setExporting(null);
    }
  };

  const toggleSection = (cat: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  };

  const warnMsg =
    result.vision_error ||
    result.boq_error ||
    (totalArea < 100 ? "Total area looks low — verify scale and units." : null) ||
    (result.extraction_quality?.level === "low" ? "Low confidence extraction — verify before tender." : null);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
        <div>
          <Link
            href={`${basePath}/dashboard`}
            style={{ fontSize: 13, color: "var(--primary)", textDecoration: "none", marginBottom: 8, display: "inline-block" }}
          >
            ← Back to upload
          </Link>
          <h2 className="page-title" style={{ marginBottom: 4 }}>{job.file_name}</h2>
          <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
            {result.method_used} · {new Date(job.created_at).toLocaleString("en-IN")}
          </p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
            {result.building_type && <span className="badge badge-info">{result.building_type}</span>}
            {result.drawing_type && <span className="badge badge-muted">{result.drawing_type}</span>}
            {result.vision_used && <span className="badge badge-success">Vision AI</span>}
            {result.source_type && <span className="badge badge-muted">{result.source_type.toUpperCase()}</span>}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {(["csv", "xlsx", "pdf"] as const).map((fmt) => (
            <button
              key={fmt}
              type="button"
              className="btn btn-secondary"
              disabled={!boqItems.length || !!exporting}
              onClick={() => void handleExport(fmt)}
            >
              {exporting === fmt ? "…" : `Export ${fmt.toUpperCase()}`}
            </button>
          ))}
        </div>
      </div>

      {warnMsg && <div className="alert alert-warning">{warnMsg}</div>}

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Built-up area</div>
          <div className="stat-value primary">
            {totalArea > 0 ? `${totalArea.toLocaleString("en-IN")} sq ft` : "—"}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Rooms</div>
          <div className="stat-value">{roomData.length || "—"}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Cost / sq ft</div>
          <div className="stat-value">
            {costPerSqft > 0 ? `₹${costPerSqft.toLocaleString("en-IN")}` : "—"}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">BOQ total (incl. GST)</div>
          <div className="stat-value primary">
            {(gst?.grand_total_with_gst ?? editedTotal ?? boqTotal) > 0
              ? `₹${Number(gst?.grand_total_with_gst ?? editedTotal ?? boqTotal).toLocaleString("en-IN")}`
              : "—"}
          </div>
        </div>
      </div>

      {(result.wall_thickness || result.scale_detection || result.rates_basis) && (
        <div className="card">
          <div className="card-body" style={{ display: "flex", flexWrap: "wrap", gap: 24, fontSize: 13 }}>
            {result.wall_thickness && (
              <span>
                <strong>Walls:</strong> ext {result.wall_thickness.external_mm}mm · int{" "}
                {result.wall_thickness.internal_mm}mm
              </span>
            )}
            {result.scale_detection?.scale_ratio && (
              <span>
                <strong>Scale:</strong> {result.scale_detection.scale_ratio}
              </span>
            )}
            {result.rates_basis && (
              <span>
                <strong>Rates:</strong> {result.rates_basis}
              </span>
            )}
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-body">
          <div className="tabs">
            {(["overview", "boq", "rooms"] as const).map((tab) => (
              <button
                key={tab}
                type="button"
                className={`tab ${activeTab === tab ? "active" : ""}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab === "boq" ? "Bill of Quantities" : tab === "rooms" ? "Room schedule" : "Summary"}
              </button>
            ))}
          </div>

          {activeTab === "overview" && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 24 }}>
              <div>
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Detected spaces</h3>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {(result.rooms_found?.length ? result.rooms_found : roomData.map((r) => r.room)).map(
                    (r) => (
                      <span key={r} className="badge badge-info">
                        {r}
                      </span>
                    ),
                  )}
                  {!roomData.length && !result.rooms_found?.length && (
                    <span style={{ color: "var(--text-muted)" }}>None detected</span>
                  )}
                </div>
              </div>
              <div>
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Cost by section</h3>
                {Object.entries(boqSummary)
                  .filter(([, v]) => Number(v) > 0)
                  .map(([k, v]) => (
                    <div
                      key={k}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "8px 0",
                        borderBottom: "1px solid var(--border)",
                        fontSize: 13,
                      }}
                    >
                      <span style={{ color: "var(--text-secondary)" }}>{k}</span>
                      <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600, color: "var(--success)" }}>
                        ₹{Number(v).toLocaleString("en-IN")}
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {activeTab === "boq" && (
            <div>
              {gst && (
                <div className="stat-grid" style={{ marginBottom: 20 }}>
                  {[
                    ["Material", gst.material_subtotal],
                    ["Labour", gst.labour_subtotal],
                    [`GST (${gst.gst_pct ?? 18}%)`, gst.gst_amount],
                    ["Grand total", gst.grand_total_with_gst],
                  ].map(([label, val]) => (
                    <div key={String(label)} className="stat-card">
                      <div className="stat-label">{label}</div>
                      <div className="stat-value">
                        {val != null ? `₹${Number(val).toLocaleString("en-IN")}` : "—"}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>
                {boqItems.length} line items — edit quantity and rate for contractor adjustments
              </p>
              {Object.entries(grouped).map(([category, items]) => {
                const catTotal = items.reduce((s, i) => s + i.amount, 0);
                const open = expandedSections.has(category);
                return (
                  <div key={category} style={{ marginBottom: 12 }}>
                    <button type="button" className="collapse-trigger" onClick={() => toggleSection(category)}>
                      <span>{category}</span>
                      <span style={{ fontFamily: "var(--font-mono)", color: "var(--primary)" }}>
                        ₹{catTotal.toLocaleString("en-IN")} {open ? "▼" : "▶"}
                      </span>
                    </button>
                    {open && (
                      <div style={{ overflowX: "auto", border: "1px solid var(--border)", borderRadius: 8 }}>
                        <table className="data-table">
                          <thead>
                            <tr>
                              {["#", "Description", "Unit", "Qty", "Rate (₹)", "Amount (₹)"].map((h) => (
                                <th key={h}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {items.map((item) => (
                              <tr key={item.sno}>
                                <td>{item.sno}</td>
                                <td style={{ maxWidth: 280 }}>
                                  {item.description}
                                  {item.notes && (
                                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
                                      {item.notes}
                                    </div>
                                  )}
                                </td>
                                <td>{item.unit}</td>
                                <td>
                                  <input
                                    className="table-input"
                                    type="number"
                                    value={item.qty || ""}
                                    onChange={(e) => updateBoqField(item.sno, "qty", e.target.value)}
                                    style={{ width: 80 }}
                                  />
                                </td>
                                <td>
                                  <input
                                    className="table-input"
                                    type="number"
                                    value={item.rate || ""}
                                    onChange={(e) => updateBoqField(item.sno, "rate", e.target.value)}
                                    style={{ width: 96 }}
                                  />
                                </td>
                                <td style={{ fontWeight: 600, fontFamily: "var(--font-mono)" }}>
                                  {item.amount > 0 ? item.amount.toLocaleString("en-IN") : "—"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {activeTab === "rooms" && (
            <div style={{ overflowX: "auto" }}>
              <table className="data-table">
                <thead>
                  <tr>
                    {["Room", "Width (ft)", "Height (ft)", "Area (sq ft)", "Floor", "Source"].map((h) => (
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
                        <td style={{ fontWeight: 600, color: "var(--primary)" }}>{r.area}</td>
                        <td>{r.floor ?? "—"}</td>
                        <td style={{ fontSize: 12, color: "var(--text-muted)" }}>{r.source}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>
                        No room data extracted
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
