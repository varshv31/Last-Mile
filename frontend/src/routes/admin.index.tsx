import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Package } from "lucide-react";
import { Button } from "@/components/ui/button";
import { RoleGuard } from "@/components/role-guard";
import { CardsSkeleton, EmptyState, ErrorState, LoadingRows, PageHeader } from "@/components/states";
import { StatusBadge } from "@/components/status-badge";
import { adminApi } from "@/lib/api-client";
import type { OrderStatus } from "@/lib/api-types";
import { formatCurrency, formatDateTime } from "@/lib/format";

export const Route = createFileRoute("/admin/")({
  head: () => ({
    meta: [
      { title: "Operations Overview — SwiftRoute Admin" },
      {
        name: "description",
        content:
          "Monitor live delivery volume, unassigned orders, failures and revenue across the last-mile network.",
      },
      { property: "og:title", content: "Operations Overview — SwiftRoute Admin" },
      { property: "og:description", content: "Live delivery operations at a glance." },
    ],
  }),
  component: () => (
    <RoleGuard role="ADMIN">
      <AdminOverview />
    </RoleGuard>
  ),
});

const ACTIVE: OrderStatus[] = ["CREATED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY"];

function StatCard({
  label,
  value,
  tone,
  hint,
}: {
  label: string;
  value: string;
  tone?: string | undefined;
  hint?: string | undefined;
}) {
  return (
    <div className="card-surface p-4 sm:p-5">
      <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${tone ?? "text-foreground"}`}>{value}</p>
      {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

function AdminOverview() {
  const ordersQuery = useQuery({
    queryKey: ["admin", "orders", { limit: 100, offset: 0 }],
    queryFn: () => adminApi.listOrders({ limit: 100, offset: 0 }),
    staleTime: 30_000,
  });

  const zonesQuery = useQuery({
    queryKey: ["admin", "zones", { limit: 100, offset: 0 }],
    queryFn: () => adminApi.listZones({ limit: 100, offset: 0 }),
    staleTime: 300_000,
  });

  const orders = ordersQuery.data ?? [];
  const active = orders.filter((o) => ACTIVE.includes(o.status));
  const unassigned = orders.filter((o) => !o.assigned_agent_id && ACTIVE.includes(o.status));
  const failed = orders.filter((o) => o.status === "FAILED");
  const delivered = orders.filter((o) => o.status === "DELIVERED");
  const revenue = orders
    .filter((o) => o.status !== "CANCELLED")
    .reduce((sum, o) => sum + (o.total_charge ?? 0), 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Operations overview"
        description="Latest 100 orders across the network."
        actions={
          <Button asChild>
            <Link to="/admin/orders">
              <Package className="size-4" />
              Manage orders
            </Link>
          </Button>
        }
      />

      {ordersQuery.isError ? (
        <ErrorState error={ordersQuery.error} onRetry={() => void ordersQuery.refetch()} />
      ) : ordersQuery.isPending ? (
        <CardsSkeleton />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Active orders" value={String(active.length)} tone="text-accent" />
          <StatCard
            label="Awaiting agent"
            value={String(unassigned.length)}
            tone={unassigned.length ? "text-warning-foreground" : undefined}
            hint="Active orders with no agent"
          />
          <StatCard
            label="Failed"
            value={String(failed.length)}
            tone={failed.length ? "text-destructive" : undefined}
          />
          <StatCard label="Billed value" value={formatCurrency(revenue)} />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <section className="card-surface p-4 sm:p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-base font-semibold">Recent orders</h2>
            <Button asChild variant="ghost" size="sm">
              <Link to="/admin/orders">
                View all
                <ArrowRight className="size-4" />
              </Link>
            </Button>
          </div>

          {ordersQuery.isPending ? (
            <LoadingRows rows={5} />
          ) : orders.length === 0 ? (
            <EmptyState
              title="No orders yet"
              description="Orders created by customers will appear here."
            />
          ) : (
            <ul className="divide-y divide-border">
              {orders.slice(0, 8).map((order) => (
                <li key={order.id}>
                  <Link
                    to="/admin/orders/$orderId"
                    params={{ orderId: order.id }}
                    className="flex flex-col gap-2 rounded-lg px-2 py-3 transition-colors hover:bg-secondary/60 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold">{order.order_number}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatDateTime(order.created_at)} · {order.order_type} ·{" "}
                        {order.payment_type}
                        {order.assigned_agent_id ? "" : " · unassigned"}
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
        </section>

        <aside className="space-y-4">
          <div className="card-surface p-4 sm:p-5">
            <h2 className="text-base font-semibold">Network</h2>
            <dl className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Zones configured</dt>
                <dd className="font-medium">{zonesQuery.data?.length ?? "—"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Delivered (recent)</dt>
                <dd className="font-medium">{delivered.length}</dd>
              </div>
            </dl>
            <div className="mt-4 grid gap-2">
              <Button asChild variant="outline" size="sm">
                <Link to="/admin/zones">Zones &amp; areas</Link>
              </Button>
              <Button asChild variant="outline" size="sm">
                <Link to="/admin/rates">Rate cards</Link>
              </Button>
              <Button asChild variant="outline" size="sm">
                <Link to="/admin/cod-surcharges">COD surcharges</Link>
              </Button>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
