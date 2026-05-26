"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useUser, useOrganization } from "@clerk/nextjs";
import { createBrowserSupabaseClient } from "@/lib/supabase/client";

type RoomData = { room: string; area: number; floor?: string; };
type BOQItem = { sno: string; description: string; unit: string; qty: number; rate: number; amount: number; category: string; notes?: string; };
type AnalysisResult = {
  source_type?: string; method_used?: string; rooms_found?: string[];
  room_data?: RoomData[]; total_area?: number; costs?: Record<string, number>;
  building_type?: string; rates_basis?: string; cost_per_sqft?: number;
  boq_total?: number; boq_items?: BOQItem[]; boq_summary?: Record<string, number>;
  vision_used?: boolean; floor_count?: number; drawing_type?: string;
  features_found?: string[];
};
type Job = {
  id: string; file_name: string; file_path: string; file_type: string | null;
  status: "queued" | "processing" | "completed" | "failed";
  result: AnalysisResult | null; error: string | null;
  created_at: string; user_id?: string; org_id?: string;
};

const COLS = "id,file_name,file_path,file_type,status,result,error,created_at,user_id,org_id";
const mono: React.CSSProperties = { fontFamily: "var(--font-mono)" };

function fileIcon(name: string) {
  const n = name.toLowerCase();
  if (n.endsWith('.pdf')) return '📄';
  if (n.endsWith('.dxf') || n.endsWith('.dwg')) return '📐';
  if (n.endsWith('.jpg') || n.endsWith('.jpeg') || n.endsWith('.png')) return '🖼';
  return '📁';
}

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === "completed"
      ? "badge-success"
      : status === "failed"
        ? "badge-danger"
        : status === "processing"
          ? "badge-info"
          : "badge-warning";
  return <span className={`badge ${cls}`}>{status}</span>;
}

function JobDetailPanel({ job, onClose }: { job: Job; onClose: () => void }) {
  const result = job.result;
  const boqItems = result?.boq_items ?? [];
  const boqTotal = result?.boq_total ?? 0;
  const boqSummary = result?.boq_summary ?? result?.costs ?? {};
  const roomData = result?.room_data ?? [];
  const [activeTab, setActiveTab] = useState<'overview' | 'rooms' | 'boq'>('overview');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  const grouped = boqItems.reduce((acc, item) => {
    if (!acc[item.category]) acc[item.category] = [];
    acc[item.category].push(item);
    return acc;
  }, {} as Record<string, BOQItem[]>);

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 100, display: 'flex' }}>
      {/* Backdrop */}
      <div onClick={onClose} style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)' }} />

      {/* Drawer */}
      <div style={{
        position: 'relative', marginLeft: 'auto', width: '100%', maxWidth: 780,
        background: 'var(--bg-surface)', borderLeft: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column', height: '100%', overflowY: 'auto',
        animation: 'slideIn 0.25s ease',
      }}>
        {/* Header */}
        <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--border)', background: 'var(--bg-elevated)', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, flexShrink: 0 }}>
          <div style={{ overflow: 'hidden', flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <span style={{ fontSize: 20 }}>{fileIcon(job.file_name)}</span>
              <StatusBadge status={job.status} />
              {result?.vision_used && <span style={{ ...mono, fontSize: 10, color: 'var(--green)', background: 'var(--green-dim)', padding: '3px 8px', borderRadius: 100, border: '1px solid rgba(0,229,160,0.2)' }}>Gemini Vision</span>}
            </div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: 20, color: 'var(--text-primary)', marginBottom: 4, wordBreak: 'break-all' }}>{job.file_name}</h2>
            <p style={{ ...mono, fontSize: 11, color: 'var(--text-muted)' }}>
              {new Date(job.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
              {' · '}{job.id.slice(0, 8)}
            </p>
          </div>
          <button onClick={onClose} style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10, width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: 16, flexShrink: 0 }}>✕</button>
        </div>

        {/* Failed state */}
        {job.status === 'failed' && (
          <div style={{ margin: '24px 32px', padding: '16px 20px', borderRadius: 14, background: 'rgba(255,68,68,0.08)', border: '1px solid rgba(255,68,68,0.2)', color: '#FF6B6B', fontSize: 13 }}>
            <strong>Analysis failed:</strong> {job.error ?? 'Unknown error'}
          </div>
        )}

        {/* No result */}
        {job.status === 'completed' && !result && (
          <div style={{ margin: '24px 32px', padding: '16px 20px', borderRadius: 14, background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-muted)', fontSize: 13 }}>
            No analysis data available for this job.
          </div>
        )}

        {/* Result */}
        {result && (
          <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 12 }}>
              {[
                { label: 'Total Area', value: result.total_area ? `${result.total_area} sq ft` : '—', accent: true },
                { label: 'Rooms', value: String(roomData.length || (result.rooms_found?.length ?? 0)) },
                { label: 'BOQ Cost', value: boqTotal > 0 ? `₹${(boqTotal / 100000).toFixed(1)}L` : '—', accent: true },
                { label: 'Cost/Sq Ft', value: result.cost_per_sqft ? `₹${result.cost_per_sqft}` : '—' },
              ].map(s => (
                <div key={s.label} style={{ borderRadius: 14, border: '1px solid var(--border)', background: 'var(--bg-card)', padding: '16px 18px' }}>
                  <p style={{ ...mono, fontSize: 10, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.label}</p>
                  <p style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 900, color: s.accent ? 'var(--accent)' : 'var(--text-primary)', letterSpacing: '-0.03em' }}>{s.value}</p>
                </div>
              ))}
            </div>

            {/* Info pills */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {result.building_type && <span style={{ ...mono, fontSize: 10, padding: '4px 10px', borderRadius: 100, background: 'rgba(255,107,43,0.08)', color: 'var(--accent-2)', border: '1px solid rgba(255,107,43,0.2)' }}>{result.building_type}</span>}
              {result.drawing_type && <span style={{ ...mono, fontSize: 10, padding: '4px 10px', borderRadius: 100, background: 'var(--accent-glow)', color: 'var(--accent)', border: '1px solid rgba(0,212,255,0.2)' }}>{result.drawing_type}</span>}
              {result.floor_count && <span style={{ ...mono, fontSize: 10, padding: '4px 10px', borderRadius: 100, background: 'var(--bg-elevated)', color: 'var(--text-secondary)', border: '1px solid var(--border)' }}>{result.floor_count} floors</span>}
            </div>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: 4, borderRadius: 12, padding: 4, background: 'var(--bg-elevated)', border: '1px solid var(--border)', width: 'fit-content' }}>
              {(['overview', 'rooms', 'boq'] as const).map(tab => (
                <button key={tab} onClick={() => setActiveTab(tab)} style={{
                  padding: '7px 18px', borderRadius: 8, fontSize: 12, fontWeight: 700,
                  border: 'none', cursor: 'pointer', fontFamily: 'var(--font-display)',
                  background: activeTab === tab ? 'var(--accent)' : 'transparent',
                  color: activeTab === tab ? 'var(--bg-base)' : 'var(--text-secondary)',
                  transition: 'all 0.15s', textTransform: 'capitalize',
                }}>
                  {tab === 'boq' ? 'BOQ' : tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            {/* Overview tab */}
            {activeTab === 'overview' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {(result.rooms_found?.length ?? 0) > 0 && (
                  <div style={{ borderRadius: 14, border: '1px solid var(--border)', background: 'var(--bg-card)', padding: 18 }}>
                    <p style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 14, color: 'var(--text-primary)', marginBottom: 12 }}>Rooms Detected</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                      {result.rooms_found!.map(r => (
                        <span key={r} style={{ ...mono, fontSize: 11, padding: '4px 10px', borderRadius: 100, background: 'var(--accent-glow)', color: 'var(--accent)', border: '1px solid rgba(0,212,255,0.2)' }}>{r}</span>
                      ))}
                    </div>
                  </div>
                )}
                {Object.keys(boqSummary).length > 0 && (
                  <div style={{ borderRadius: 14, border: '1px solid var(--border)', background: 'var(--bg-card)', padding: 18 }}>
                    <p style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 14, color: 'var(--text-primary)', marginBottom: 12 }}>Cost Breakdown</p>
                    {Object.entries(boqSummary).filter(([, v]) => v > 0).map(([k, v]) => (
                      <div key={k} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                        <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{k}</span>
                        <span style={{ ...mono, fontSize: 12, fontWeight: 700, color: 'var(--green)' }}>₹{Number(v).toLocaleString('en-IN')}</span>
                      </div>
                    ))}
                    {boqTotal > 0 && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 12, marginTop: 4 }}>
                        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 14, color: 'var(--text-primary)' }}>Grand Total</span>
                        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: 20, color: 'var(--accent)' }}>₹{boqTotal.toLocaleString('en-IN')}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Rooms tab */}
            {activeTab === 'rooms' && (
              <div style={{ borderRadius: 14, border: '1px solid var(--border)', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: 'var(--bg-elevated)' }}>
                      {['Room', 'Area (sq ft)', 'Floor'].map(h => (
                        <th key={h} style={{ padding: '10px 14px', textAlign: 'left', ...mono, fontSize: 10, color: 'var(--text-muted)', fontWeight: 400 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {roomData.length > 0 ? roomData.map((r, i) => (
                      <tr key={i} style={{ borderTop: '1px solid var(--border)', background: i % 2 === 0 ? 'var(--bg-card)' : 'var(--bg-elevated)' }}>
                        <td style={{ padding: '10px 14px', fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{r.room}</td>
                        <td style={{ padding: '10px 14px', ...mono, fontSize: 12, fontWeight: 700, color: 'var(--accent)' }}>{r.area}</td>
                        <td style={{ padding: '10px 14px', fontSize: 12, color: 'var(--text-secondary)' }}>{r.floor ?? '—'}</td>
                      </tr>
                    )) : (
                      <tr><td colSpan={3} style={{ padding: '32px', textAlign: 'center', ...mono, fontSize: 12, color: 'var(--text-muted)' }}>No room data</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {/* BOQ tab */}
            {activeTab === 'boq' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{boqItems.length} items · {result.rates_basis}</p>
                  <button onClick={() => setExpandedSections(new Set(Object.keys(grouped)))}
                    style={{ ...mono, fontSize: 11, color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer' }}>Expand all</button>
                </div>
                {Object.entries(grouped).map(([cat, items]) => {
                  const total = items.reduce((s, i) => s + i.amount, 0);
                  const open = expandedSections.has(cat);
                  return (
                    <div key={cat} style={{ borderRadius: 12, border: '1px solid var(--border)', overflow: 'hidden' }}>
                      <button onClick={() => setExpandedSections(prev => { const n = new Set(prev); n.has(cat) ? n.delete(cat) : n.add(cat); return n; })}
                        style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: 'var(--bg-elevated)', border: 'none', cursor: 'pointer' }}>
                        <span style={{ fontFamily: 'var(--font-display)', fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>{cat}</span>
                        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                          <span style={{ ...mono, fontSize: 12, fontWeight: 700, color: 'var(--accent)' }}>₹{total.toLocaleString('en-IN')}</span>
                          <span style={{ ...mono, fontSize: 9, color: 'var(--text-muted)' }}>{open ? '▲' : '▼'}</span>
                        </div>
                      </button>
                      {open && items.map((item, i) => (
                        <div key={item.sno} style={{ padding: '10px 16px', borderTop: '1px solid var(--border)', background: i % 2 === 0 ? 'var(--bg-card)' : 'var(--bg-elevated)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                          <div style={{ flex: 1 }}>
                            <p style={{ fontSize: 12, color: 'var(--text-primary)', marginBottom: 2 }}>{item.description}</p>
                            {item.notes && <p style={{ ...mono, fontSize: 10, color: 'var(--text-muted)' }}>{item.notes}</p>}
                            <p style={{ ...mono, fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>{item.qty > 0 ? `${item.qty.toFixed(2)} ${item.unit}` : ''} {item.rate > 0 ? `@ ₹${item.rate}` : ''}</p>
                          </div>
                          <span style={{ ...mono, fontSize: 12, fontWeight: 700, color: item.amount > 0 ? 'var(--green)' : 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                            {item.amount > 0 ? `₹${item.amount.toLocaleString('en-IN')}` : 'Ref'}
                          </span>
                        </div>
                      ))}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
      <style>{`@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }`}</style>
    </div>
  );
}

const FILTERS = ['all', 'completed', 'failed', 'pdf', 'dxf', 'dwg', 'image'] as const;
type Filter = typeof FILTERS[number];

export default function AnalysesHistory({ isOrg = false }: { isOrg?: boolean }) {
  const router = useRouter();
  const base = isOrg ? "/org" : "";
  const { user } = useUser();
  const { organization } = useOrganization();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<Filter>('all');
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  const fetchJobs = useCallback(async () => {
    if (!user) return;
    const sb = createBrowserSupabaseClient();
    let q = sb.from('analysis_jobs').select(COLS).order('created_at', { ascending: false }).limit(100);
    if (isOrg && organization) q = q.eq('org_id', organization.id);
    else q = q.eq('user_id', user.id).is('org_id', null);
    const { data } = await q;
    if (data) setJobs(data as Job[]);
    setLoading(false);
  }, [user, organization, isOrg]);

  useEffect(() => { void fetchJobs(); }, [fetchJobs]);

  const filtered = jobs.filter(j => {
    const matchSearch = j.file_name.toLowerCase().includes(search.toLowerCase());
    const matchFilter =
      filter === 'all' ? true :
      filter === 'completed' ? j.status === 'completed' :
      filter === 'failed' ? j.status === 'failed' :
      filter === 'pdf' ? j.file_name.toLowerCase().endsWith('.pdf') :
      filter === 'dxf' ? j.file_name.toLowerCase().endsWith('.dxf') :
      filter === 'dwg' ? j.file_name.toLowerCase().endsWith('.dwg') :
      filter === 'image' ? /\.(jpg|jpeg|png)$/i.test(j.file_name) : true;
    return matchSearch && matchFilter;
  });

  const stats = {
    total: jobs.length,
    completed: jobs.filter(j => j.status === 'completed').length,
    failed: jobs.filter(j => j.status === 'failed').length,
    totalArea: jobs.reduce((s, j) => s + (j.result?.total_area ?? 0), 0),
  };

  return (
    <div>

      {/* Summary stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16, marginBottom: 32 }}>
        {[
          { label: 'Total Analyses', value: stats.total, accent: false },
          { label: 'Completed', value: stats.completed, accent: true },
          { label: 'Failed', value: stats.failed, accent: false, warn: stats.failed > 0 },
          { label: 'Total Area Analysed', value: `${stats.totalArea.toLocaleString('en-IN')} sq ft`, accent: true },
        ].map(s => (
          <div key={s.label} style={{ borderRadius: 18, border: '1px solid var(--border)', background: 'var(--bg-card)', padding: '20px 22px' }}>
            <p style={{ ...mono, fontSize: 10, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{s.label}</p>
            <p style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 900, letterSpacing: '-0.03em', color: s.warn ? '#FF6B6B' : s.accent ? 'var(--accent)' : 'var(--text-primary)' }}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Search + Filter bar */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center', flexWrap: 'wrap' }}>
        {/* Search */}
        <div style={{ position: 'relative', flex: 1, minWidth: 200 }}>
          <span style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', fontSize: 14, opacity: 0.4 }}>🔍</span>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by file name…"
            style={{ width: '100%', paddingLeft: 40, paddingRight: 16, paddingTop: 10, paddingBottom: 10, borderRadius: 12, border: '1px solid var(--border)', background: 'var(--bg-card)', color: 'var(--text-primary)', fontSize: 13, fontFamily: 'var(--font-body)', outline: 'none', boxSizing: 'border-box' }}
          />
        </div>

        {/* Filter pills */}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {FILTERS.map(f => (
            <button key={f} onClick={() => setFilter(f)} style={{
              padding: '8px 16px', borderRadius: 100, fontSize: 12, fontWeight: 600,
              border: '1px solid', cursor: 'pointer', fontFamily: 'var(--font-body)',
              transition: 'all 0.15s',
              background: filter === f ? 'var(--accent)' : 'var(--bg-card)',
              color: filter === f ? 'var(--bg-base)' : 'var(--text-secondary)',
              borderColor: filter === f ? 'var(--accent)' : 'var(--border)',
            }}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        <button onClick={fetchJobs} style={{ padding: '10px 16px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--bg-card)', color: 'var(--text-secondary)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-body)' }}>
          ↻ Refresh
        </button>
      </div>

      {/* Results count */}
      <p style={{ ...mono, fontSize: 11, color: 'var(--text-muted)', marginBottom: 12 }}>
        {filtered.length} result{filtered.length !== 1 ? 's' : ''} {search || filter !== 'all' ? '(filtered)' : ''}
      </p>

      {/* Job list */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)', ...mono, fontSize: 13 }}>Loading analyses…</div>
      ) : filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px', borderRadius: 20, border: '1px dashed var(--border)', background: 'var(--bg-card)' }}>
          <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.2 }}>📋</div>
          <p style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 8 }}>No analyses found</p>
          <p style={{ ...mono, fontSize: 12, color: 'var(--text-muted)' }}>{search ? 'Try a different search term' : 'Upload a blueprint on the Dashboard to get started'}</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {/* Table header */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 100px', gap: 12, padding: '8px 20px', ...mono, fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            <span>File</span><span>Date</span><span>Area</span><span>BOQ Cost</span><span>Status</span>
          </div>

          {filtered.map(j => (
            <div
              key={j.id}
              onClick={() => {
                if (j.status === "completed") {
                  router.push(`${base}/dashboard/analysis/${j.id}`);
                } else {
                  setSelectedJob(j);
                }
              }}
              style={{
                display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 100px',
                gap: 12, alignItems: 'center',
                padding: '16px 20px', borderRadius: 16,
                border: '1px solid var(--border)', background: 'var(--bg-card)',
                cursor: 'pointer', transition: 'all 0.15s',
              }}
              onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border-bright)'; (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-elevated)'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border)'; (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-card)'; }}
            >
              {/* File name */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, overflow: 'hidden' }}>
                <span style={{ fontSize: 18, flexShrink: 0 }}>{fileIcon(j.file_name)}</span>
                <div style={{ overflow: 'hidden' }}>
                  <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{j.file_name}</p>
                  {j.result?.building_type && <p style={{ ...mono, fontSize: 10, color: 'var(--text-muted)' }}>{j.result.building_type}</p>}
                </div>
              </div>

              {/* Date */}
              <span style={{ ...mono, fontSize: 11, color: 'var(--text-muted)' }}>
                {new Date(j.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: '2-digit' })}
              </span>

              {/* Area */}
              <span style={{ ...mono, fontSize: 12, color: j.result?.total_area ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                {j.result?.total_area ? `${j.result.total_area} sqft` : '—'}
              </span>

              {/* BOQ cost */}
              <span style={{ ...mono, fontSize: 12, color: j.result?.boq_total ? 'var(--green)' : 'var(--text-muted)', fontWeight: j.result?.boq_total ? 700 : 400 }}>
                {j.result?.boq_total ? `₹${(j.result.boq_total / 100000).toFixed(1)}L` : '—'}
              </span>

              {/* Status */}
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <StatusBadge status={j.status} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Detail drawer */}
      {selectedJob && <JobDetailPanel job={selectedJob} onClose={() => setSelectedJob(null)} />}
    </div>
  );
}