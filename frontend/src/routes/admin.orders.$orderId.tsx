import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { ArrowLeft, Loader2, ShieldAlert, UserPlus, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Field } from "@/components/address-fields";
import { OrderChargeBreakdown } from "@/components/charge-breakdown";
import { RoleGuard } from "@/components/role-guard";
import { ErrorState, LoadingRows, PageHeader } from "@/components/states";
import { StatusBadge } from "@/components/status-badge";
import { AddressCard, OrderMetaGrid } from "@/routes/orders.$orderId";
import { adminApi } from "@/lib/api-client";
import { ORDER_STATUSES, type AssignmentResponse, type OrderStatus } from "@/lib/api-types";
import { formatDateTime, titleCase } from "@/lib/format";

export const Route = createFileRoute("/admin/orders/$orderId")({
  head: () => ({
    meta: [
      { title: "Order Management — SwiftRoute Admin" },
      {
        name: "description",
        content:
          "Assign delivery agents, auto-assign the nearest available agent and override order status with an audit reason.",
      },
      { property: "og:title", content: "Order Management — SwiftRoute Admin" },
      { property: "og:description", content: "Agent assignment and status overrides." },
    ],
  }),
  component: () => (
    <RoleGuard role="ADMIN">
      <AdminOrderDetail />
    </RoleGuard>
  ),
});

function AdminOrderDetail() {
  const { orderId } = Route.useParams();
  const queryClient = useQueryClient();
  const [agentId, setAgentId] = useState("");
  const [overrideStatus, setOverrideStatus] = useState<OrderStatus>("CANCELLED");
  const [reason, setReason] = useState("");
  const [assignment, setAssignment] = useState<AssignmentResponse | null>(null);

  const orderQuery = useQuery({
    queryKey: ["admin", "order", orderId],
    queryFn: () => adminApi.getOrder(orderId),
  });

  const invalidate = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["admin", "order", orderId] }),
      queryClient.invalidateQueries({ queryKey: ["admin", "orders"] }),
    ]);
  };

  const assign = useMutation({
    mutationFn: () => adminApi.assignAgent(orderId, agentId.trim()),
    onSuccess: async (res) => {
      setAssignment(res);
      setAgentId("");
      toast.success(`Assigned to ${res.agent_name}`);
      await invalidate();
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const autoAssign = useMutation({
    mutationFn: () => adminApi.autoAssign(orderId),
    onSuccess: async (res) => {
      setAssignment(res);
      toast.success(
        `Auto-assigned to ${res.agent_name}${
          res.distance_km !== null ? ` · ${res.distance_km} km away` : ""
        }`,
      );
      await invalidate();
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const override = useMutation({
    mutationFn: () =>
      adminApi.overrideStatus(orderId, { status: overrideStatus, reason: reason.trim() }),
    onSuccess: async (order) => {
      toast.success(`Status overridden to ${titleCase(order.status)}`);
      setReason("");
      await invalidate();
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (orderQuery.isPending) {
    return (
      <div className="space-y-6">
        <PageHeader title="Order" />
        <LoadingRows rows={5} />
      </div>
    );
  }

  if (orderQuery.isError) {
    return (
      <div className="space-y-6">
        <PageHeader title="Order" />
        <ErrorState error={orderQuery.error} onRetry={() => void orderQuery.refetch()} />
      </div>
    );
  }

  const order = orderQuery.data;
  const pickup = order.addresses.find((a) => a.address_type === "PICKUP");
  const drop = order.addresses.find((a) => a.address_type === "DROP");
  const busy = assign.isPending || autoAssign.isPending || override.isPending;

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link to="/admin/orders">
          <ArrowLeft className="size-4" />
          Back to orders
        </Link>
      </Button>

      <PageHeader
        title={order.order_number}
        description={`Created ${formatDateTime(order.created_at)}`}
        actions={<StatusBadge status={order.status} />}
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <section className="card-surface p-4 sm:p-6">
            <h2 className="mb-4 text-base font-semibold">Route</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <AddressCard address={pickup} label="Pickup" />
              <AddressCard address={drop} label="Drop" />
            </div>
            <div className="mt-5 border-t border-border pt-5">
              <OrderMetaGrid order={order} />
            </div>
          </section>

          <section className="card-surface p-4 sm:p-6">
            <h2 className="text-base font-semibold">Agent assignment</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {order.assigned_agent_id
                ? `Currently assigned to agent ${order.assigned_agent_id}`
                : "No agent assigned yet."}
            </p>

            <div className="mt-4 grid gap-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
              <Field id="agent-id" label="Agent user ID" hint="The agent's USER UUID.">
                <Input
                  id="agent-id"
                  value={agentId}
                  disabled={busy}
                  placeholder="3fa85f64-5717-4562-b3fc-2c963f66afa6"
                  onChange={(e) => setAgentId(e.target.value)}
                />
              </Field>
              <Button
                disabled={!agentId.trim() || busy}
                onClick={() => assign.mutate()}
                className="sm:mb-0"
              >
                {assign.isPending ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <UserPlus className="size-4" />
                )}
                Assign
              </Button>
            </div>

            <div className="mt-4 border-t border-border pt-4">
              <Button variant="outline" disabled={busy} onClick={() => autoAssign.mutate()}>
                {autoAssign.isPending ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Zap className="size-4" />
                )}
                Auto-assign nearest agent
              </Button>
            </div>

            {assignment ? (
              <dl className="mt-4 grid gap-3 rounded-lg bg-secondary/60 p-4 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-xs text-muted-foreground">Agent</dt>
                  <dd className="font-medium">{assignment.agent_name}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Type</dt>
                  <dd className="font-medium">{titleCase(assignment.assignment_type)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Distance</dt>
                  <dd className="font-medium">
                    {assignment.distance_km !== null ? `${assignment.distance_km} km` : "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Assigned at</dt>
                  <dd className="font-medium">{formatDateTime(assignment.assigned_at)}</dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-xs text-muted-foreground">Reason</dt>
                  <dd className="font-medium">{assignment.reason}</dd>
                </div>
              </dl>
            ) : null}
          </section>

          <section className="card-surface p-4 sm:p-6">
            <h2 className="flex items-center gap-2 text-base font-semibold">
              <ShieldAlert className="size-4 text-warning-foreground" />
              Status override
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Bypasses the state machine and writes an audit log entry.
            </p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <Field label="Target status">
                <Select
                  value={overrideStatus}
                  disabled={busy}
                  onValueChange={(v) => setOverrideStatus(v as OrderStatus)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ORDER_STATUSES.map((s) => (
                      <SelectItem key={s} value={s}>
                        {titleCase(s)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
              <Field
                id="reason"
                label="Reason"
                hint="Minimum 5 characters, stored in the audit log."
                className="sm:col-span-2"
              >
                <Textarea
                  id="reason"
                  rows={3}
                  value={reason}
                  disabled={busy}
                  placeholder="e.g. Customer requested cancellation via support ticket #1234"
                  onChange={(e) => setReason(e.target.value)}
                />
              </Field>
            </div>
            <Button
              variant="destructive"
              className="mt-4"
              disabled={reason.trim().length < 5 || busy}
              onClick={() => override.mutate()}
            >
              {override.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
              Override status
            </Button>
          </section>
        </div>

        <aside className="space-y-6">
          <section className="card-surface p-4 sm:p-5">
            <h2 className="mb-4 text-base font-semibold">Charges</h2>
            <OrderChargeBreakdown order={order} />
          </section>

          <section className="card-surface p-4 sm:p-5">
            <h2 className="mb-3 text-base font-semibold">Identifiers</h2>
            <dl className="space-y-2 text-xs">
              <div>
                <dt className="text-muted-foreground">Order ID</dt>
                <dd className="break-all font-mono">{order.id}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Customer ID</dt>
                <dd className="break-all font-mono">{order.customer_id}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Assigned agent</dt>
                <dd className="break-all font-mono">{order.assigned_agent_id ?? "—"}</dd>
              </div>
            </dl>
          </section>
        </aside>
      </div>
    </div>
  );
}
