"use client";

import Link from "next/link";
import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function LandingPage() {
  const { isSignedIn, isLoaded } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (isLoaded && isSignedIn) router.push("/auth-redirect");
  }, [isLoaded, isSignedIn, router]);

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-page)" }}>
      <header
        style={{
          background: "var(--bg-surface)",
          borderBottom: "1px solid var(--border)",
          padding: "14px 32px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              background: "linear-gradient(135deg, var(--primary), var(--accent))",
              color: "#fff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: 13,
            }}
          >
            BR
          </span>
          <span style={{ fontWeight: 700, fontSize: 16 }}>Blueprint Reader</span>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <Link href="/sign-in" className="btn btn-ghost">
            Sign in
          </Link>
          <Link href="/sign-up" className="btn btn-primary">
            Get started
          </Link>
        </div>
      </header>

      <section style={{ maxWidth: 960, margin: "0 auto", padding: "64px 24px", textAlign: "center" }}>
        <p
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: "var(--primary)",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            marginBottom: 16,
          }}
        >
          Indian construction · DSR BOQ
        </p>
        <h1 style={{ fontSize: "clamp(32px, 5vw, 48px)", fontWeight: 700, lineHeight: 1.15, marginBottom: 16 }}>
          Blueprint to Bill of Quantities
          <br />
          <span style={{ color: "var(--primary)" }}>in one professional workflow</span>
        </h1>
        <p style={{ fontSize: 16, color: "var(--text-secondary)", maxWidth: 560, margin: "0 auto 32px", lineHeight: 1.6 }}>
          Upload DXF, IFC, PDF, or site photos. Get room schedules, GST-ready BOQ, and export to Excel — built for architects and QS teams in India.
        </p>
        <Link href="/sign-up" className="btn btn-primary" style={{ padding: "12px 28px", fontSize: 15 }}>
          Open workspace →
        </Link>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: 16,
            marginTop: 64,
            textAlign: "left",
          }}
        >
          {[
            { t: "Multi-format import", d: "DXF, IFC, PDF, PNG, JPG" },
            { t: "DSR rate schedules", d: "Maharashtra, Delhi, GST split" },
            { t: "Dedicated reports", d: "Separate pages per analysis" },
            { t: "Contractor-ready export", d: "CSV, Excel, PDF" },
          ].map((f) => (
            <div key={f.t} className="card" style={{ padding: 20 }}>
              <p style={{ fontWeight: 600, marginBottom: 6 }}>{f.t}</p>
              <p style={{ fontSize: 13, color: "var(--text-muted)" }}>{f.d}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
