import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { Loader2, Truck } from "lucide-react";
import { homePathForRole, useAuth } from "@/lib/auth";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "SwiftRoute — Last-Mile Delivery Management Platform" },
      {
        name: "description",
        content:
          "SwiftRoute is a last-mile delivery platform for customers, delivery agents and operations admins: zone pricing, live tracking and agent assignment.",
      },
      { property: "og:title", content: "SwiftRoute — Last-Mile Delivery Management" },
      {
        property: "og:description",
        content:
          "Create shipments, track deliveries in real time and manage zones, rate cards and agents.",
      },
    ],
  }),
  component: Index,
});

function Index() {
  const { status, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (status === "authenticated" && user) {
      void navigate({ to: homePathForRole(user.role), replace: true });
    } else if (status === "unauthenticated") {
      void navigate({ to: "/login", replace: true });
    }
  }, [status, user, navigate]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background">
      <div className="flex size-12 items-center justify-center rounded-xl bg-accent text-accent-foreground">
        <Truck className="size-6" />
      </div>
      <h1 className="text-lg font-semibold">SwiftRoute</h1>
      <Loader2 className="size-5 animate-spin text-muted-foreground" />
    </div>
  );
}
