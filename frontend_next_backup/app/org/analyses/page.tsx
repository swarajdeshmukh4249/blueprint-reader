import AppShell from "@/components/layout/AppShell";
import AnalysesHistory from "@/components/AnalysesHistory";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export default async function OrgAnalysesPage() {
  const { userId, orgId } = await auth();
  if (!userId) redirect("/sign-in");
  if (!orgId) redirect("/dashboard");

  return (
    <AppShell title="Team project history" subtitle="Organisation blueprint analyses">
      <AnalysesHistory isOrg={true} />
    </AppShell>
  );
}
