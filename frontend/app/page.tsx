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
    <main
      style={{
        minHeight: "100vh",
        background: "var(--cad-bg-app)",
        display: "flex",
        flexDirection: "column",
      }}
      className="cad-viewport-grid"
    >
      <header className="cad-titlebar" style={{ padding: "0 20px" }}>
        <div className="cad-titlebar-app">
          <span
            style={{
              width: 16,
              height: 16,
              background: "var(--cad-accent)",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 9,
              fontWeight: 800,
              color: "#fff",
            }}
          >
            B
          </span>
          Blueprint<span className="accent">Reader</span>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          <Link
            href="/sign-in"
            style={{
              fontSize: 12,
              color: "var(--cad-text)",
              padding: "2px 12px",
              textDecoration: "none",
            }}
          >
            Sign in
          </Link>
          <Link
            href="/sign-up"
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: "#fff",
              background: "var(--cad-blue)",
              padding: "4px 14px",
              borderRadius: 2,
              textDecoration: "none",
            }}
          >
            Start workspace
          </Link>
        </div>
      </header>

      <section
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "48px 24px",
          textAlign: "center",
          position: "relative",
          zIndex: 1,
        }}
      >
        <p
          style={{
            fontFamily: "var(--font-mono-cad)",
            fontSize: 11,
            color: "var(--cad-text-dim)",
            marginBottom: 16,
            letterSpacing: "0.08em",
          }}
        >
          INDIAN CONSTRUCTION · DSR BOQ · DXF / IFC
        </p>
        <h1
          style={{
            fontSize: "clamp(32px, 6vw, 56px)",
            fontWeight: 600,
            color: "var(--cad-text-bright)",
            lineHeight: 1.15,
            marginBottom: 16,
            maxWidth: 720,
          }}
        >
          Read any blueprint.
          <br />
          <span style={{ color: "var(--cad-accent)" }}>Output tender-ready BOQ.</span>
        </h1>
        <p
          style={{
            fontSize: 15,
            color: "var(--cad-text-dim)",
            maxWidth: 520,
            lineHeight: 1.6,
            marginBottom: 32,
          }}
        >
          AutoCAD-style workspace for architects and QS teams — room detection, wall
          thickness, GST breakdown, and Maharashtra / Delhi DSR rates in one flow.
        </p>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "center" }}>
          <Link
            href="/sign-up"
            style={{
              padding: "10px 28px",
              background: "var(--cad-blue)",
              color: "#fff",
              fontWeight: 600,
              fontSize: 13,
              textDecoration: "none",
              borderRadius: 2,
            }}
          >
            Open workspace →
          </Link>
          <Link
            href="/sign-in"
            style={{
              padding: "10px 28px",
              border: "1px solid var(--cad-border-light)",
              color: "var(--cad-text)",
              fontSize: 13,
              textDecoration: "none",
              borderRadius: 2,
              background: "var(--cad-bg-ribbon)",
            }}
          >
            Sign in
          </Link>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: 12,
            maxWidth: 900,
            marginTop: 64,
            width: "100%",
          }}
        >
          {[
            { title: "DXF + IFC import", desc: "Industry CAD and BIM formats" },
            { title: "DSR-compliant BOQ", desc: "Material · labour · GST split" },
            { title: "Editable quantities", desc: "Contractor-ready line items" },
            { title: "Export CSV / Excel / PDF", desc: "Tender documentation" },
          ].map((f) => (
            <div
              key={f.title}
              style={{
                padding: 16,
                border: "1px solid var(--cad-border)",
                background: "var(--cad-bg-panel)",
                textAlign: "left",
                borderRadius: 2,
              }}
            >
              <p style={{ fontWeight: 600, color: "var(--cad-text-bright)", marginBottom: 6, fontSize: 13 }}>
                {f.title}
              </p>
              <p style={{ fontSize: 12, color: "var(--cad-text-dim)" }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <footer
        style={{
          borderTop: "1px solid var(--cad-border)",
          padding: "12px 24px",
          fontSize: 11,
          color: "var(--cad-text-dim)",
          textAlign: "center",
          fontFamily: "var(--font-mono-cad)",
        }}
      >
        © 2026 Blueprint Reader · Built for Indian construction
      </footer>
    </main>
  );
}
