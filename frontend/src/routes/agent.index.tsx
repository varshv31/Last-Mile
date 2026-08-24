import { createFileRoute, Link } from "@tanstack/react-router";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Crosshair, Loader2, PackageCheck, Truck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Field } from "@/components/address-fields";
import { RoleGuard } from "@/components/role-guard";
import {
  EmptyState,
  ErrorState,
  LoadingRows,
  PageHeader,
  PaginationBar,
} from "@/components/states";
import { AvailabilityBadge, StatusBadge } from "@/components/status-badge";
import { agentApi } from "@/lib/api-client";
import type { AvailabilityStatus, OrderResponse } from "@/lib/api-types";
import { formatCurrency, formatDateTime } from "@/lib/format";

export const Route = createFileRoute("/agent/")({
  head: () => ({
    meta: [
      { title: "My Deliveries — SwiftRoute Agent" },
      {
        name: "description",
        content:
          "Set your availability, update your location and work through the delivery orders assigned to you.",
      },
      { property: "og:title", content: "My Deliveries — SwiftRoute Agent" },
      { property: "og:description", content: "Assigned deliveries and availability controls." },
    ],
  }),
  component: () => (
    <RoleGuard role="AGENT">
      <AgentHome />
    </RoleGuard>
  ),
});

const LIMIT = 20;
const ACTIVE = ["CREATED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY"];

export function AgentOrderList({ orders }: { orders: OrderResponse[] }) {
  return (
    <ul className="divide-y divide-border">
      {orders.map((order) => {
        const drop = order.addresses.find((a) => a.address_type === "DROP");
        return (
          <li key={order.id}>
            <Link
              to="/agent/orders/$orderId"
              params={{ orderId: order.id }}
              className="flex flex-col gap-2 rounded-lg px-2 py-3 transition-colors hover:bg-secondary/60 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-foreground">
                  {order.order_number}
                </p>
                <p className="truncate text-xs text-muted-foreground">
                  {drop ? `${drop.address_line1}, ${drop.city} ${drop.postal_code}` : "—"}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {formatDateTime(order.created_at)} · {order.payment_type} ·{" "}
                  {formatCurrency(order.total_charge)}
                </p>
              </div>
              <StatusBadge status={order.status} />
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

function AvailabilityCard() {
  const queryClient = useQueryClient();
  const profile = useQuery({ queryKey: ["agent", "profile"], queryFn: agentApi.profile });
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");

  const setAvailability = useMutation({
    mutationFn: (status: AvailabilityStatus) => agentApi.updateAvailability(status),
    onSuccess: async (data) => {
      queryClient.setQueryData(["agent", "profile"], data);
      toast.success(`You are now ${data.availability_status.toLowerCase()}`);
      await queryClient.invalidateQueries({ queryKey: ["agent", "orders"] });
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const updateLocation = useMutation({
    mutationFn: () =>
      agentApi.updateLocation({ latitude: Number(lat), longitude: Number(lng) }),
    onSuccess: (data) => {
      queryClient.setQueryData(["agent", "profile"], data);
      toast.success("Location updated");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const useDeviceLocation = () => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      toast.error("Geolocation is not available on this device.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLat(pos.coords.latitude.toFixed(6));
        setLng(pos.coords.longitude.toFixed(6));
        toast.success("Coordinates captured — save to update.");
      },
      () => toast.error("Could not read your location."),
    );
  };

  return (
    <section className="card-surface p-4 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Availability</h2>
          <p className="text-sm text-muted-foreground">
            Only available agents receive auto-assigned orders.
          </p>
        </div>
        {profile.data ? <AvailabilityBadge status={profile.data.availability_status} /> : null}
      </div>

      {profile.isError ? (
        <div className="mt-4">
          <ErrorState error={profile.error} onRetry={() => void profile.refetch()} />
        </div>
      ) : null}

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <Field label="Status">
          <Select
            value={profile.data?.availability_status ?? "OFFLINE"}
            disabled={profile.isPending || setAvailability.isPending}
            onValueChange={(v) => setAvailability.mutate(v as AvailabilityStatus)}
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="AVAILABLE">Available</SelectItem>
              <SelectItem value="BUSY">Busy</SelectItem>
              <SelectItem value="OFFLINE">Offline</SelectItem>
            </SelectContent>
          </Select>
        </Field>

        <div className="grid grid-cols-2 gap-3">
          <Field id="lat" label="Latitude">
            <Input
              id="lat"
              value={lat}
              inputMode="decimal"
              placeholder={profile.data?.current_latitude?.toString() ?? "19.0760"}
              onChange={(e) => setLat(e.target.value)}
            />
          </Field>
          <Field id="lng" label="Longitude">
            <Input
              id="lng"
              value={lng}
              inputMode="decimal"
              placeholder={profile.data?.current_longitude?.toString() ?? "72.8777"}
              onChange={(e) => setLng(e.target.value)}
            />
          </Field>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button variant="outline" size="sm" onClick={useDeviceLocation}>
          <Crosshair className="size-4" />
          Use my location
        </Button>
        <Button
          size="sm"
          disabled={!lat || !lng || updateLocation.isPending}
          onClick={() => updateLocation.mutate()}
        >
          {updateLocation.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
          Save location
        </Button>
      </div>
    </section>
  );
}

function AgentHome() {
  const [offset, setOffset] = useState(0);

  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ["agent", "orders", { limit: LIMIT, offset }],
    queryFn: () => agentApi.listOrders({ limit: LIMIT, offset }),
    placeholderData: keepPreviousData,
    staleTime: 15_000,
  });

  const active = useMemo(
    () => (data ?? []).filter((o) => ACTIVE.includes(o.status)),
    [data],
  );

  return (
    <div className="space-y-6">
      <PageHeader title="My deliveries" description="Assigned orders and availability." />

      <AvailabilityCard />

      <section className="card-surface p-4 sm:p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold">Active assignments</h2>
          <Button asChild variant="ghost" size="sm">
            <Link to="/agent/history">
              <PackageCheck className="size-4" />
              History
            </Link>
          </Button>
        </div>

        {isError ? (
          <ErrorState error={error} onRetry={() => void refetch()} />
        ) : isPending ? (
          <LoadingRows rows={4} />
        ) : active.length === 0 ? (
          <EmptyState
            title="No active deliveries"
            description="New orders will appear here once they are assigned to you."
            icon={<Truck className="size-5" />}
          />
        ) : (
          <>
            <AgentOrderList orders={active} />
            <PaginationBar
              offset={offset}
              limit={LIMIT}
              count={(data ?? []).length}
              onChange={setOffset}
            />
          </>
        )}
      </section>
    </div>
  );
}
