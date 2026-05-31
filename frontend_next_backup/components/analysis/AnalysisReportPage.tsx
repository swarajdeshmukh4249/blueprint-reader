"use client";

import { useEffect, useState } from "react";
import { useUser } from "@clerk/nextjs";
import { createBrowserSupabaseClient } from "@/lib/supabase/client";
import AppShell from "@/components/layout/AppShell";
import AnalysisView from "@/components/analysis/AnalysisView";
import { JOB_COLS, type AnalysisJob } from "@/lib/analysis-types";

export default function AnalysisReportPage({
  jobId,
  isOrg,
}: {
  jobId: string;
  isOrg: boolean;
}) {
  const { user } = useUser();
  const basePath = isOrg ? "/org" : "";
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user || !jobId) return;
    const sb = createBrowserSupabaseClient();
    const load = async () => {
      const { data, error: err } = await sb
        .from("analysis_jobs")
        .select(JOB_COLS)
        .eq("id", jobId)
        .single();
      if (err || !data) {
        setError("Analysis not found");
        return;
      }
      setJob(data as AnalysisJob);
    };
    void load();
  }, [user, jobId]);

  return (
    <AppShell title="Analysis report" subtitle={job?.file_name ?? "Loading…"}>
      {error && <div className="alert alert-error">{error}</div>}
      {job && <AnalysisView job={job} basePath={basePath} />}
      {!job && !error && (
        <div className="card" style={{ padding: 48, textAlign: "center" }}>
          <span className="spinner" style={{ margin: "0 auto" }} />
        </div>
      )}
    </AppShell>
  );
}
