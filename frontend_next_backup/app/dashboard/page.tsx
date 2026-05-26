import AppShell from "@/components/layout/AppShell";
import UploadWorkspace from "@/components/workspace/UploadWorkspace";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export default async function DashboardPage() {
  const { userId, orgId } = await auth();
  if (!userId) redirect("/sign-in");
  if (orgId) redirect("/org/dashboard");

  return (
    <AppShell title="Workspace" subtitle="Upload and analyze architectural drawings">
      <UploadWorkspace isOrg={false} />
    </AppShell>
  );
}
