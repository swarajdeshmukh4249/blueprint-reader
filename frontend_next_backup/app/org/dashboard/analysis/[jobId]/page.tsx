import AnalysisReportPage from "@/components/analysis/AnalysisReportPage";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export default async function OrgAnalysisPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { userId, orgId } = await auth();
  if (!userId) redirect("/sign-in");
  if (!orgId) redirect("/dashboard");
  const { jobId } = await params;
  return <AnalysisReportPage jobId={jobId} isOrg={true} />;
}
