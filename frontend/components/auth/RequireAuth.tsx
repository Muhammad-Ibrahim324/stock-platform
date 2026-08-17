"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/Button";
import { PulseBlock } from "@/components/dashboard/Skeletons";

export function RequireAuth({ children, title }: { children: ReactNode; title: string }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6">
        <PulseBlock className="mb-6 h-8 w-48" />
        <PulseBlock className="h-64 w-full" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="mx-auto flex w-full max-w-[1400px] flex-1 flex-col items-center justify-center gap-3 px-4 py-24 text-center sm:px-6">
        <h1 className="font-display text-xl font-semibold text-ink">Log in to see your {title.toLowerCase()}</h1>
        <p className="max-w-sm text-sm text-ink-muted">
          Your {title.toLowerCase()} is saved to your account so it&apos;s there next time you visit.
        </p>
        <div className="mt-3 flex gap-2">
          <Link href="/login">
            <Button variant="secondary">Log in</Button>
          </Link>
          <Link href="/signup">
            <Button variant="primary">Sign up</Button>
          </Link>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
