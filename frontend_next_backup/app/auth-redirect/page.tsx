"use client";

import { useOrganization, useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function AuthRedirect() {
  const { isLoaded: userLoaded, isSignedIn } = useUser();
  const { isLoaded: orgLoaded, organization } = useOrganization();
  const router = useRouter();

  useEffect(() => {
    if (!userLoaded || !orgLoaded) return;

    if (!isSignedIn) {
      router.push("/sign-in");
      return;
    }

    // If user is currently in an org context → org dashboard
    // Otherwise → individual dashboard
    if (organization) {
      router.push("/org/dashboard");
    } else {
      router.push("/dashboard");
    }
  }, [userLoaded, orgLoaded, isSignedIn, organization, router]);

  return (
    <main className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="text-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-900 mx-auto" />
        <p className="mt-4 text-slate-500 text-sm">Setting up your workspace...</p>
      </div>
    </main>
  );
}