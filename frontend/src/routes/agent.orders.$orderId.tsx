import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { AlertTriangle, ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Field } from "@/components/address-fields";
import { OrderChargeBreakdown } from "@/components/charge-breakdown";
import { RoleGuard } from "@/components/role-guard";
import { ErrorState, LoadingRows, PageHeader } from "@/components/states";
import { StatusBadge } from "@/components/status-badge";
import { AddressCard, OrderMetaGrid } from "@/routes/orders.$orderId";
import { agentApi } from "@/lib/api-client";
import { FAILURE_REASONS, type FailureReason, type OrderStatus } from "@/lib/api-types";
import { formatDateTime, titleCase } from "@/lib/format";

export const Route = createFileRoute("/agent/orders/$orderId")({
  head: () => ({
    meta: [
      { title: "Delivery Details — SwiftRoute Agent" },
      {
        name: "description",
        content:
          "Pickup and drop details for an assigned delivery, with status progression and failed-delivery reporting.",
      },
      { property: "og:title", content: "Delivery Details — SwiftRoute Agent" },
      { property: "og:description", content: "Advance delivery status or report a failure." },
    ],
  }),
  component: () => (
    <RoleGuard role="AGENT">
      <AgentOrderDetail />
    </RoleGuard>
  ),
});

/** State machine from the API docs. */
const NEXT_STATUS: Partial<Record<OrderStatus, OrderStatus[]>> = {
  CREATED: ["PICKED_UP", "CANCELLED"],
  PICKED_UP: ["IN_TRANSIT", "CANCELLED"],
  IN_TRANSIT: ["OUT_FOR_DELIVERY", "CANCELLED"],
  OUT_FOR_DELIVERY: ["DELIVERED"],
};

function AgentOrderDetail() {
  const { orderId } = Route.useParams();
  const queryClient = useQueryClient();
  const [remarks, setRemarks] = useState("");
  const [failOpen, setFailOpen] = useState(false);
  const [reason, setReason] = useState<FailureReason>("CUSTOMER_NOT_AVAILABLE");
  const [failRemarks, setFailRemarks] = useState("");

  const orderQuery = useQuery({
    queryKey: ["agent", "order", orderId],
    queryFn: () => agentApi.getOrder(orderId),
  });

  const invalidate = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["agent", "order", orderId] }),
      queryClient.invalidateQueries({ queryKey: ["agent", "orders"] }),
    ]);
  };

  const updateStatus = useMutation({
    mutationFn: (status: OrderStatus) =>
      agentApi.updateOrderStatus(orderId, {
        status,
        ...(remarks.trim() ? { remarks: remarks.trim() } : {}),
      }),
    onSuccess: async (order) => {
      toast.success(`Status updated to ${titleCase(order.status)}`);
      setRemarks("");
      await invalidate();
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const failDelivery = useMutation({
    mutationFn: () =>
      agentApi.failOrder(orderId, {
        reason,
        ...(failRemarks.trim() ? { remarks: failRemarks.trim() } : {}),
      }),
    onSuccess: async () => {
      toast.success("Delivery marked as failed");
      setFailOpen(false);
      setFailRemarks("");
      await invalidate();
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (orderQuery.isPending) {
    return (
      <div className="space-y-6">
        <PageHeader title="Delivery" />
        <LoadingRows rows={5} />
      </div>
    );
  }

  if (orderQuery.isError) {
    return (
      <div className="space-y-6">
        <PageHeader title="Delivery" />
        <ErrorState error={orderQuery.error} onRetry={() => void orderQuery.refetch()} />
      </div>
    );
  }

  const order = orderQuery.data;
  const pickup = order.addresses.find((a) => a.address_type === "PICKUP");
  const drop = order.addresses.find((a) => a.address_type === "DROP");
  const nextOptions = NEXT_STATUS[order.status] ?? [];
  const busy = updateStatus.isPending || failDelivery.isPending;

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link to="/agent">
          <ArrowLeft className="size-4" />
          Back to deliveries
        </Link>
      </Button>

      <PageHeader
        title={order.order_number}
        description={`Assigned order · created ${formatDateTime(order.created_at)}`}
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
            <h2 className="text-base font-semibold">Update status</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Only valid transitions from {titleCase(order.status)} are shown.
            </p>

            {nextOptions.length === 0 ? (
              <p className="mt-4 rounded-lg border border-dashed border-border px-4 py-5 text-center text-sm text-muted-foreground">
                This delivery is closed. No further status changes are possible.
              </p>
            ) : (
              <>
                <div className="mt-4">
                  <Field id="remarks" label="Remarks (optional)">
                    <Textarea
                      id="remarks"
                      value={remarks}
                      disabled={busy}
                      rows={3}
                      placeholder="e.g. Package collected from sender"
                      onChange={(e) => setRemarks(e.target.value)}
                    />
                  </Field>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {nextOptions.map((status) => (
                    <Button
                      key={status}
                      variant={status === "CANCELLED" ? "outline" : "default"}
                      disabled={busy}
                      onClick={() => updateStatus.mutate(status)}
                    >
                      {updateStatus.isPending ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        <ArrowRight className="size-4" />
                      )}
                      Mark {titleCase(status)}
                    </Button>
                  ))}
                </div>
              </>
            )}

            {order.status === "OUT_FOR_DELIVERY" ? (
              <div className="mt-5 rounded-lg border border-destructive/25 bg-destructive/5 p-4">
                <p className="text-sm font-medium text-foreground">Could not deliver?</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Report a failure with a reason. You will be released from this order.
                </p>
                <Button
                  variant="destructive"
                  size="sm"
                  className="mt-3"
                  disabled={busy}
                  onClick={() => setFailOpen(true)}
                >
                  <AlertTriangle className="size-4" />
                  Report failed delivery
                </Button>
              </div>
            ) : null}
          </section>
        </div>

        <aside className="space-y-6">
          <section className="card-surface p-4 sm:p-5">
            <h2 className="mb-4 text-base font-semibold">Charges</h2>
            <OrderChargeBreakdown order={order} />
            {order.payment_type === "COD" ? (
              <p className="mt-4 rounded-lg bg-warning/15 px-3 py-2 text-sm text-warning-foreground">
                Collect cash on delivery.
              </p>
            ) : null}
          </section>

          {order.package ? (
            <section className="card-surface p-4 sm:p-5">
              <h2 className="mb-3 text-base font-semibold">Package</h2>
              <p className="text-sm text-muted-foreground">
                {order.package.length_cm} × {order.package.breadth_cm} ×{" "}
                {order.package.height_cm} cm · {order.package.actual_weight_kg} kg
              </p>
            </section>
          ) : null}
        </aside>
      </div>

      <Dialog open={failOpen} onOpenChange={setFailOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Report failed delivery</DialogTitle>
            <DialogDescription>
              {order.order_number} will be marked as failed and the customer can reschedule.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Field label="Reason">
              <Select value={reason} onValueChange={(v) => setReason(v as FailureReason)}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FAILURE_REASONS.map((r) => (
                    <SelectItem key={r} value={r}>
                      {titleCase(r)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <Field id="fail-remarks" label="Remarks (optional)">
              <Textarea
                id="fail-remarks"
                rows={3}
                value={failRemarks}
                onChange={(e) => setFailRemarks(e.target.value)}
                placeholder="What happened at the doorstep?"
              />
            </Field>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setFailOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={failDelivery.isPending}
              onClick={() => failDelivery.mutate()}
            >
              {failDelivery.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
              Mark failed
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
