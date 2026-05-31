"use client";

import Link from "next/link";
import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import BlueprintGrid from "@/components/graphics/BlueprintGrid";
import FloorPlanSchematic from "@/components/graphics/FloorPlanSchematic";

const FEATURES = [
  { icon: "⬡", t: "Multi-format import", d: "DXF, DWG, IFC, PDF, PNG, JPG — CAD-first parsing" },
  { icon: "₹", t: "DSR rate schedules", d: "Maharashtra PWD, Delhi, GST split BOQ" },
  { icon: "◫", t: "Scientific extraction", d: "TEXT-ROOMS layer, area statements, accuracy scoring" },
  { icon: "↗", t: "Contractor export", d: "CSV, Excel, PDF with letterhead" },
];

export default function LandingPage() {
  const { isSignedIn, isLoaded } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (isLoaded && isSignedIn) router.push("/auth-redirect");
  }, [isLoaded, isSignedIn, router]);

  return (
    <div className="landing-page">
      <div className="landing-grid">
        <BlueprintGrid opacity={1} />
      </div>

      <header className="landing-header">
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span className="nav-brand-mark">BR</span>
          <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 17 }}>
            Blueprint Reader
          </span>
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

      <section className="landing-hero">
        <div>
          <p className="eyebrow">Indian construction intelligence</p>
          <h1>
            Blueprint to
            <br />
            <span>Bill of Quantities</span>
          </h1>
          <p style={{ fontSize: 16, color: "var(--text-secondary)", lineHeight: 1.65, marginBottom: 32 }}>
            Upload architectural drawings. Get room schedules, built-up areas, and GST-ready BOQ —
            engineered for architects and quantity surveyors.
          </p>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <Link href="/sign-up" className="btn btn-coral" style={{ padding: "14px 28px", fontSize: 15 }}>
              Open workspace →
            </Link>
            <Link href="/sign-in" className="btn btn-secondary">
              Sign in
            </Link>
          </div>
        </div>

        <div className="landing-hero-visual" style={{ color: "var(--ink)", opacity: 0.85 }}>
          <div
            style={{
              background: "var(--paper)",
              border: "1px solid var(--border)",
              borderRadius: 20,
              padding: 32,
              boxShadow: "var(--shadow-md)",
            }}
          >
            <FloorPlanSchematic style={{ width: "100%", height: "auto" }} />
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginTop: 20,
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                color: "var(--text-muted)",
              }}
            >
              <span>SCALE 1:100</span>
              <span style={{ color: "var(--coral)" }}>NET AREA · SQ FT</span>
            </div>
          </div>
        </div>
      </section>

      <div className="landing-feature-grid">
        {FEATURES.map((f) => (
          <div key={f.t} className="landing-feature-card">
            <div className="landing-feature-icon">{f.icon}</div>
            <p style={{ fontFamily: "var(--font-display)", fontWeight: 700, marginBottom: 8, fontSize: 15 }}>
              {f.t}
            </p>
            <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.5 }}>{f.d}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
