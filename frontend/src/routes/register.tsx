import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Loader2, Truck } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ApiError, authApi } from "@/lib/api-client";
import type { UserRole } from "@/lib/api-types";
import { homePathForRole, useAuth } from "@/lib/auth";

export const Route = createFileRoute("/register")({
  head: () => ({
    meta: [
      { title: "Create account — SwiftRoute Delivery Platform" },
      {
        name: "description",
        content:
          "Create a SwiftRoute account as a customer, delivery agent, or administrator to start managing last-mile shipments.",
      },
      { property: "og:title", content: "Create account — SwiftRoute" },
      {
        property: "og:description",
        content: "Register for the SwiftRoute last-mile delivery management platform.",
      },
    ],
  }),
  component: RegisterPage,
});

function RegisterPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    password: "",
    role: "CUSTOMER" as UserRole,
  });
  const [submitting, setSubmitting] = useState(false);

  const update = (key: keyof typeof form, value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }
    setSubmitting(true);
    try {
      await authApi.register({
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
        role: form.role,
        ...(form.phone.trim() ? { phone: form.phone.trim() } : {}),
      });
      const me = await login(form.email.trim(), form.password);
      toast.success("Account created");
      void navigate({ to: homePathForRole(me.role), replace: true });
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Unable to create account");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 flex items-center gap-2.5">
          <div className="flex size-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
            <Truck className="size-5" />
          </div>
          <span className="text-base font-semibold">SwiftRoute</span>
        </div>

        <div className="card-surface p-6 sm:p-8">
          <h1 className="text-2xl font-semibold tracking-tight">Create your account</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Choose the workspace that matches your role.
          </p>

          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full name</Label>
              <Input
                id="name"
                required
                minLength={2}
                value={form.name}
                onChange={(e) => update("name", e.target.value)}
                placeholder="Priya Sharma"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                required
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                placeholder="priya@example.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Phone (optional)</Label>
              <Input
                id="phone"
                value={form.phone}
                onChange={(e) => update("phone", e.target.value)}
                placeholder="+919876543210"
                maxLength={20}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                required
                minLength={8}
                maxLength={128}
                value={form.password}
                onChange={(e) => update("password", e.target.value)}
                placeholder="At least 8 characters"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role">Role</Label>
              <Select value={form.role} onValueChange={(v) => update("role", v)}>
                <SelectTrigger id="role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="CUSTOMER">Customer</SelectItem>
                  <SelectItem value="AGENT">Delivery Agent</SelectItem>
                  <SelectItem value="ADMIN">Administrator</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
              Create account
            </Button>
          </form>
        </div>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Already registered?{" "}
          <Link to="/login" className="font-medium text-accent hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
