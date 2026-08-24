import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Loader2, Truck } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { homePathForRole, useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api-client";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign in — SwiftRoute Delivery Platform" },
      {
        name: "description",
        content:
          "Sign in to SwiftRoute to create shipments, run deliveries, or manage last-mile operations.",
      },
      { property: "og:title", content: "Sign in — SwiftRoute Delivery Platform" },
      {
        property: "og:description",
        content: "Access your customer, delivery agent, or admin workspace.",
      },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const { login, user, status } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (status === "authenticated" && user) {
      void navigate({ to: homePathForRole(user.role), replace: true });
    }
  }, [status, user, navigate]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const me = await login(email.trim(), password);
      toast.success(`Welcome back, ${me.name.split(" ")[0]}`);
      void navigate({ to: homePathForRole(me.role), replace: true });
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Unable to sign in");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden flex-col justify-between bg-primary p-10 text-primary-foreground lg:flex">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg bg-accent">
            <Truck className="size-5" />
          </div>
          <span className="text-lg font-semibold">SwiftRoute</span>
        </div>
        <div className="max-w-md">
          <h2 className="text-3xl font-semibold tracking-tight">
            Last-mile delivery, fully under control.
          </h2>
          <p className="mt-4 text-sm text-primary-foreground/70">
            Zone-based pricing, live tracking timelines, agent assignment and rate-card management
            in one operations platform.
          </p>
        </div>
        <p className="text-xs text-primary-foreground/50">
          Customer · Delivery Agent · Administrator
        </p>
      </div>

      <div className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <div className="flex size-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
              <Truck className="size-5" />
            </div>
            <span className="text-base font-semibold">SwiftRoute</span>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Use your SwiftRoute account to continue.
          </p>

          <form onSubmit={onSubmit} className="mt-7 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
              Sign in
            </Button>
          </form>

          <p className="mt-6 text-sm text-muted-foreground">
            No account yet?{" "}
            <Link to="/register" className="font-medium text-accent hover:underline">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
