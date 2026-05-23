import Navbar from "@/components/Navbar";
import BlueprintAnalyzer from "@/components/BlueprintAnalyzer";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export default async function DashboardPage() {
  const { userId, orgId } = await auth();
  if (!userId) redirect("/sign-in");
  if (orgId) redirect("/org/dashboard");

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: "var(--cad-bg-app)" }}>
      <Navbar />
      <BlueprintAnalyzer isOrg={false} />
    </div>
  );
}
