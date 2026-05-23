import Navbar from "@/components/Navbar";
import AnalysesHistory from "@/components/AnalysesHistory";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export default async function AnalysesPage() {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");

  return (
    <div style={{ minHeight: "100vh", background: "var(--cad-bg-app)", display: "flex", flexDirection: "column" }}>
      <Navbar />
      <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--cad-border)", background: "var(--cad-bg-ribbon)" }}>
        <p style={{ fontFamily: "var(--font-mono-cad)", fontSize: 10, color: "var(--cad-text-dim)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
          Project Manager
        </p>
        <h1 style={{ fontSize: 18, fontWeight: 600, color: "var(--cad-text-bright)", marginTop: 4 }}>
          Analysis History
        </h1>
      </div>
      <AnalysesHistory isOrg={false} />
    </div>
  );
}
