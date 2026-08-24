import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, PackagePlus, Truck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { RoleGuard } from "@/components/role-guard";
import { CardsSkeleton, EmptyState, ErrorState, LoadingRows, PageHeader } from "@/components/states";
import { StatusBadge } from "@/components/status-badge";
import { customerApi } from "@/lib/api-client";
import type { OrderResponse, OrderStatus } from "@/lib/api-types";
import { formatCurrency, formatDateTime } from "@/lib/format";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Customer Dashboard — SwiftRoute" },
      {
        name: "description",
        content:
          "Track your shipments, view delivery charges and monitor active last-mile orders in one dashboard.",
      },
      { property: "og:title", content: "Customer Dashboard — SwiftRoute" },
      { property: "og:description", content: "Your shipment overview and live delivery status." },
    ],
  }),
  component: () => (
    <RoleGuard role="CUSTOMER">
      <CustomerDashboard />
    </RoleGuard>
  ),
});

const ACTIVE: OrderStatus[] = ["CREATED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY"];

function StatCard({ label, value, tone }: { label: string; value: string; tone?: string | undefined }) {
  return (
    <div className="card-surface p-4 sm:p-5">
      <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${tone ?? "text-foreground"}`}>{value}</p>
    </div>
  );
}

function CustomerDashboard() {
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ["customer", "orders", { limit: 100, offset: 0 }],
    queryFn: () => customerApi.listOrders({ limit: 100, offset: 0 }),
    staleTime: 30_000,
  });

  const orders: OrderResponse[] = data ?? [];
  const active = orders.filter((o) => ACTIVE.includes(o.status));
  const delivered = orders.filter((o) => o.status === "DELIVERED");
  const failed = orders.filter((o) => o.status === "FAILED");
  const spend = orders
    .filter((o) => o.status !== "CANCELLED")
    .reduce((sum, o) => sum + (o.total_charge ?? 0), 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Your shipments at a glance."
        actions={
          <Button asChild>
            <Link to="/orders/new">
              <PackagePlus className="size-4" />
              New shipment
            </Link>
          </Button>
        }
      />

      {isError ? <ErrorState error={error} onRetry={() => void refetch()} /> : null}

      {isPending ? (
        <CardsSkeleton />
      ) : !isError ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Active shipments" value={String(active.length)} tone="text-accent" />
          <StatCard label="Delivered" value={String(delivered.length)} tone="text-success" />
          <StatCard
            label="Failed deliveries"
            value={String(failed.length)}
            tone={failed.length ? "text-destructive" : undefined}
          />
          <StatCard label="Total billed" value={formatCurrency(spend)} />
        </div>
      ) : null}

      <div className="card-surface p-4 sm:p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold">Recent shipments</h2>
          <Button asChild variant="ghost" size="sm">
            <Link to="/orders">
              View all
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>

        {isPending ? (
          <LoadingRows rows={4} />
        ) : orders.length === 0 ? (
          <EmptyState
            title="No shipments yet"
            description="Create your first delivery order to see it tracked here."
            icon={<Truck className="size-5" />}
            action={
              <Button asChild>
                <Link to="/orders/new">Create shipment</Link>
              </Button>
            }
          />
        ) : (
          <ul className="divide-y divide-border">
            {orders.slice(0, 6).map((order) => (
              <li key={order.id}>
                <Link
                  to="/orders/$orderId"
                  params={{ orderId: order.id }}
                  className="flex flex-col gap-2 py-3 transition-colors hover:bg-secondary/50 sm:flex-row sm:items-center sm:justify-between sm:rounded-lg sm:px-2"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-foreground">
                      {order.order_number}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDateTime(order.created_at)} · {order.order_type} ·{" "}
                      {order.payment_type}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium">
                      {formatCurrency(order.total_charge)}
                    </span>
                    <StatusBadge status={order.status} />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
