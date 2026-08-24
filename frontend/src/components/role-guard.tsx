import type { ReactNode } from "react";
import { Loader2 } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { useRequireRole } from "@/lib/auth";
import type { UserRole } from "@/lib/api-types";

function FullPageLoader() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <Loader2 className="size-6 animate-spin text-accent" />
    </div>
  );
}

export function RoleGuard({ role, children }: { role: UserRole; children: ReactNode }) {
  const { ready } = useRequireRole(role);
  if (!ready) return <FullPageLoader />;
  return <AppShell>{children}</AppShell>;
}
