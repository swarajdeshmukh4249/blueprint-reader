import AppShell from "@/components/layout/AppShell";
import AnalysesHistory from "@/components/AnalysesHistory";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export default async function AnalysesPage() {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");

  return (
    <AppShell title="Project history" subtitle="All your blueprint analyses and BOQ reports">
      <AnalysesHistory isOrg={false} />
    </AppShell>
  );
}
