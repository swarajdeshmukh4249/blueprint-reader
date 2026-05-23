import AppShell from "@/components/layout/AppShell";
import UploadWorkspace from "@/components/workspace/UploadWorkspace";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export default async function OrgDashboardPage() {
  const { userId, orgId } = await auth();
  if (!userId) redirect("/sign-in");
  if (!orgId) redirect("/dashboard");

  return (
    <AppShell title="Team workspace" subtitle="Shared blueprint analyses for your organisation">
      <UploadWorkspace isOrg={true} />
    </AppShell>
  );
}
