import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { ArrowLeft, CalendarClock, Loader2, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { OrderChargeBreakdown } from "@/components/charge-breakdown";
import { OrderTimeline } from "@/components/order-timeline";
import { RoleGuard } from "@/components/role-guard";
import { ErrorState, LoadingRows, PageHeader } from "@/components/states";
import { StatusBadge } from "@/components/status-badge";
import { customerApi } from "@/lib/api-client";
import type { AddressResponse, OrderResponse } from "@/lib/api-types";
import { formatDate, formatDateTime, titleCase } from "@/lib/format";

export const Route = createFileRoute("/orders/$orderId")({
  head: () => ({
    meta: [
      { title: "Shipment Details — SwiftRoute" },
      {
        name: "description",
        content:
          "View shipment addresses, charge breakdown and the full delivery tracking timeline for your order.",
      },
      { property: "og:title", content: "Shipment Details — SwiftRoute" },
      { property: "og:description", content: "Charges, addresses and live tracking timeline." },
    ],
  }),
  component: () => (
    <RoleGuard role="CUSTOMER">
      <OrderDetail />
    </RoleGuard>
  ),
});

export function AddressCard({
  address,
  label,
}: {
  address: AddressResponse | undefined;
  label: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-secondary/40 p-4">
      <p className="flex items-center gap-1.5 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
        <MapPin className="size-3.5" /> {label}
      </p>
      {address ? (
        <div className="mt-2 space-y-0.5 text-sm">
          <p className="font-medium text-foreground">{address.name}</p>
          <p className="text-muted-foreground">{address.phone}</p>
          <p className="text-foreground/85">
            {address.address_line1}
            {address.address_line2 ? `, ${address.address_line2}` : ""}
          </p>
          <p className="text-foreground/85">
            {address.city}, {address.state} {address.postal_code}
          </p>
          <p className="text-muted-foreground">{address.country}</p>
        </div>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">Not available</p>
      )}
    </div>
  );
}

export function OrderMetaGrid({ order }: { order: OrderResponse }) {
  const items: Array<[string, string]> = [
    ["Order type", order.order_type],
    ["Payment", titleCase(order.payment_type)],
    ["Zone type", order.zone_type ? titleCase(order.zone_type) : "—"],
    ["Created", formatDateTime(order.created_at)],
    ["Confirmed", formatDateTime(order.confirmed_at)],
    ["Last updated", formatDateTime(order.updated_at)],
  ];
  return (
    <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
      {items.map(([label, value]) => (
        <div key={label}>
          <dt className="text-xs text-muted-foreground">{label}</dt>
          <dd className="mt-0.5 text-sm font-medium text-foreground">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function OrderDetail() {
  const { orderId } = Route.useParams();
  const queryClient = useQueryClient();
  const [rescheduleOpen, setRescheduleOpen] = useState(false);
  const [newDate, setNewDate] = useState("");

  const orderQuery = useQuery({
    queryKey: ["customer", "order", orderId],
    queryFn: () => customerApi.getOrder(orderId),
  });

  const trackingQuery = useQuery({
    queryKey: ["customer", "tracking", orderId],
    queryFn: () => customerApi.getTracking(orderId),
    enabled: Boolean(orderQuery.data),
  });

  const reschedule = useMutation({
    mutationFn: () => customerApi.reschedule(orderId, newDate),
    onSuccess: async (res) => {
      toast.success(`Rescheduled to ${formatDate(res.new_delivery_date)}`);
      setRescheduleOpen(false);
      setNewDate("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["customer", "order", orderId] }),
        queryClient.invalidateQueries({ queryKey: ["customer", "tracking", orderId] }),
        queryClient.invalidateQueries({ queryKey: ["customer", "orders"] }),
      ]);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (orderQuery.isPending) {
    return (
      <div className="space-y-6">
        <PageHeader title="Shipment" />
        <LoadingRows rows={5} />
      </div>
    );
  }

  if (orderQuery.isError) {
    return (
      <div className="space-y-6">
        <PageHeader title="Shipment" />
        <ErrorState error={orderQuery.error} onRetry={() => void orderQuery.refetch()} />
      </div>
    );
  }

  const order = orderQuery.data;
  const pickup = order.addresses.find((a) => a.address_type === "PICKUP");
  const drop = order.addresses.find((a) => a.address_type === "DROP");

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link to="/orders">
          <ArrowLeft className="size-4" />
          Back to orders
        </Link>
      </Button>

      <PageHeader
        title={order.order_number}
        description={`Placed ${formatDateTime(order.created_at)}`}
        actions={
          <div className="flex items-center gap-2">
            <StatusBadge status={order.status} />
            {order.status === "FAILED" ? (
              <Button size="sm" onClick={() => setRescheduleOpen(true)}>
                <CalendarClock className="size-4" />
                Reschedule
              </Button>
            ) : null}
          </div>
        }
      />

      {order.status === "FAILED" ? (
        <div className="rounded-xl border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-foreground/85">
          This delivery failed. Pick a new delivery date to have it attempted again.
        </div>
      ) : null}

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
            <h2 className="mb-4 text-base font-semibold">Tracking timeline</h2>
            {trackingQuery.isPending ? (
              <LoadingRows rows={3} />
            ) : trackingQuery.isError ? (
              <ErrorState
                error={trackingQuery.error}
                onRetry={() => void trackingQuery.refetch()}
              />
            ) : (
              <OrderTimeline events={trackingQuery.data?.timeline ?? []} />
            )}
          </section>
        </div>

        <aside className="space-y-6">
          <section className="card-surface p-4 sm:p-5">
            <h2 className="mb-4 text-base font-semibold">Charges</h2>
            <OrderChargeBreakdown order={order} />
          </section>

          {order.package ? (
            <section className="card-surface p-4 sm:p-5">
              <h2 className="mb-3 text-base font-semibold">Package</h2>
              <p className="text-sm text-muted-foreground">
                {order.package.length_cm} × {order.package.breadth_cm} ×{" "}
                {order.package.height_cm} cm
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Actual weight {order.package.actual_weight_kg} kg
              </p>
            </section>
          ) : null}
        </aside>
      </div>

      <Dialog open={rescheduleOpen} onOpenChange={setRescheduleOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reschedule delivery</DialogTitle>
            <DialogDescription>
              Choose a new delivery date for {order.order_number}.
            </DialogDescription>
          </DialogHeader>
          <div>
            <Input
              type="date"
              value={newDate}
              min={new Date().toISOString().slice(0, 10)}
              onChange={(e) => setNewDate(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRescheduleOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={!newDate || reschedule.isPending}
              onClick={() => reschedule.mutate()}
            >
              {reschedule.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
