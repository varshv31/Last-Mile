import { createFileRoute, Link } from "@tanstack/react-router";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Filter, Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Field } from "@/components/address-fields";
import { RoleGuard } from "@/components/role-guard";
import {
  EmptyState,
  ErrorState,
  LoadingRows,
  PageHeader,
  PaginationBar,
} from "@/components/states";
import { StatusBadge } from "@/components/status-badge";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { adminApi } from "@/lib/api-client";
import {
  ORDER_STATUSES,
  type AdminOrderFilters,
  type OrderStatus,
  type OrderType,
  type PaymentType,
} from "@/lib/api-types";
import { formatCurrency, formatDateTime, titleCase } from "@/lib/format";

export const Route = createFileRoute("/admin/orders/")({
  head: () => ({
    meta: [
      { title: "All Orders — SwiftRoute Admin" },
      {
        name: "description",
        content:
          "Filter delivery orders by status, zone, agent, payment type and date to manage last-mile operations.",
      },
      { property: "og:title", content: "All Orders — SwiftRoute Admin" },
      { property: "og:description", content: "Search and filter every order in the network." },
    ],
  }),
  component: () => (
    <RoleGuard role="ADMIN">
      <AdminOrders />
    </RoleGuard>
  ),
});

const LIMIT = 20;
const ALL = "ALL";

function AdminOrders() {
  const [offset, setOffset] = useState(0);
  const [showFilters, setShowFilters] = useState(false);
  const [status, setStatus] = useState<OrderStatus | typeof ALL>(ALL);
  const [orderType, setOrderType] = useState<OrderType | typeof ALL>(ALL);
  const [paymentType, setPaymentType] = useState<PaymentType | typeof ALL>(ALL);
  const [pickupZone, setPickupZone] = useState<string>(ALL);
  const [dropZone, setDropZone] = useState<string>(ALL);
  const [agentId, setAgentId] = useState("");
  const [createdFrom, setCreatedFrom] = useState("");
  const [createdTo, setCreatedTo] = useState("");
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 300);
  const debouncedAgent = useDebouncedValue(agentId, 400);

  const zonesQuery = useQuery({
    queryKey: ["admin", "zones", { limit: 100, offset: 0 }],
    queryFn: () => adminApi.listZones({ limit: 100, offset: 0 }),
    staleTime: 300_000,
  });

  const filters: AdminOrderFilters = useMemo(
    () => ({
      limit: LIMIT,
      offset,
      ...(status !== ALL ? { status } : {}),
      ...(orderType !== ALL ? { order_type: orderType } : {}),
      ...(paymentType !== ALL ? { payment_type: paymentType } : {}),
      ...(pickupZone !== ALL ? { pickup_zone_id: pickupZone } : {}),
      ...(dropZone !== ALL ? { drop_zone_id: dropZone } : {}),
      ...(debouncedAgent.trim() ? { agent_id: debouncedAgent.trim() } : {}),
      ...(createdFrom ? { created_from: `${createdFrom}T00:00:00Z` } : {}),
      ...(createdTo ? { created_to: `${createdTo}T23:59:59Z` } : {}),
    }),
    [
      offset,
      status,
      orderType,
      paymentType,
      pickupZone,
      dropZone,
      debouncedAgent,
      createdFrom,
      createdTo,
    ],
  );

  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ["admin", "orders", filters],
    queryFn: () => adminApi.listOrders(filters),
    placeholderData: keepPreviousData,
    staleTime: 15_000,
  });

  const orders = useMemo(() => {
    const term = debouncedSearch.trim().toLowerCase();
    if (!term) return data ?? [];
    return (data ?? []).filter(
      (o) =>
        o.order_number.toLowerCase().includes(term) ||
        o.addresses.some(
          (a) =>
            a.city.toLowerCase().includes(term) ||
            a.postal_code.toLowerCase().includes(term) ||
            a.name.toLowerCase().includes(term),
        ),
    );
  }, [data, debouncedSearch]);

  const resetFilters = () => {
    setStatus(ALL);
    setOrderType(ALL);
    setPaymentType(ALL);
    setPickupZone(ALL);
    setDropZone(ALL);
    setAgentId("");
    setCreatedFrom("");
    setCreatedTo("");
    setOffset(0);
  };

  const zones = zonesQuery.data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Orders"
        description="All delivery orders across the network."
        actions={
          <Button variant="outline" onClick={() => setShowFilters((v) => !v)}>
            <Filter className="size-4" />
            {showFilters ? "Hide filters" : "Filters"}
          </Button>
        }
      />

      <div className="card-surface p-4 sm:p-6">
        <div className="relative">
          <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search order number, city, postal code…"
            className="pl-9"
          />
        </div>

        {showFilters ? (
          <div className="mt-4 grid gap-4 border-t border-border pt-4 sm:grid-cols-2 lg:grid-cols-4">
            <Field label="Status">
              <Select
                value={status}
                onValueChange={(v) => {
                  setStatus(v as OrderStatus | typeof ALL);
                  setOffset(0);
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>All statuses</SelectItem>
                  {ORDER_STATUSES.map((s) => (
                    <SelectItem key={s} value={s}>
                      {titleCase(s)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            <Field label="Order type">
              <Select
                value={orderType}
                onValueChange={(v) => {
                  setOrderType(v as OrderType | typeof ALL);
                  setOffset(0);
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>All types</SelectItem>
                  <SelectItem value="B2C">B2C</SelectItem>
                  <SelectItem value="B2B">B2B</SelectItem>
                </SelectContent>
              </Select>
            </Field>

            <Field label="Payment">
              <Select
                value={paymentType}
                onValueChange={(v) => {
                  setPaymentType(v as PaymentType | typeof ALL);
                  setOffset(0);
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>All payments</SelectItem>
                  <SelectItem value="PREPAID">Prepaid</SelectItem>
                  <SelectItem value="COD">COD</SelectItem>
                </SelectContent>
              </Select>
            </Field>

            <Field id="agent" label="Agent user ID">
              <Input
                id="agent"
                value={agentId}
                placeholder="UUID"
                onChange={(e) => {
                  setAgentId(e.target.value);
                  setOffset(0);
                }}
              />
            </Field>

            <Field label="Pickup zone">
              <Select
                value={pickupZone}
                onValueChange={(v) => {
                  setPickupZone(v);
                  setOffset(0);
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>All zones</SelectItem>
                  {zones.map((z) => (
                    <SelectItem key={z.id} value={z.id}>
                      {z.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            <Field label="Drop zone">
              <Select
                value={dropZone}
                onValueChange={(v) => {
                  setDropZone(v);
                  setOffset(0);
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>All zones</SelectItem>
                  {zones.map((z) => (
                    <SelectItem key={z.id} value={z.id}>
                      {z.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            <Field id="from" label="Created from">
              <Input
                id="from"
                type="date"
                value={createdFrom}
                onChange={(e) => {
                  setCreatedFrom(e.target.value);
                  setOffset(0);
                }}
              />
            </Field>

            <Field id="to" label="Created to">
              <Input
                id="to"
                type="date"
                value={createdTo}
                onChange={(e) => {
                  setCreatedTo(e.target.value);
                  setOffset(0);
                }}
              />
            </Field>

            <div className="sm:col-span-2 lg:col-span-4">
              <Button variant="ghost" size="sm" onClick={resetFilters}>
                <X className="size-4" />
                Clear filters
              </Button>
            </div>
          </div>
        ) : null}

        <div className="mt-5">
          {isError ? (
            <ErrorState error={error} onRetry={() => void refetch()} />
          ) : isPending ? (
            <LoadingRows rows={6} />
          ) : orders.length === 0 ? (
            <EmptyState
              title="No orders match"
              description="Try widening or clearing your filters."
            />
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Order</TableHead>
                      <TableHead className="hidden md:table-cell">Route</TableHead>
                      <TableHead className="hidden sm:table-cell">Agent</TableHead>
                      <TableHead>Total</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {orders.map((order) => {
                      const pickup = order.addresses.find((a) => a.address_type === "PICKUP");
                      const drop = order.addresses.find((a) => a.address_type === "DROP");
                      return (
                        <TableRow key={order.id}>
                          <TableCell>
                            <Link
                              to="/admin/orders/$orderId"
                              params={{ orderId: order.id }}
                              className="block"
                            >
                              <span className="font-medium text-foreground">
                                {order.order_number}
                              </span>
                              <span className="block text-xs text-muted-foreground">
                                {formatDateTime(order.created_at)} · {order.order_type} ·{" "}
                                {order.payment_type}
                              </span>
                            </Link>
                          </TableCell>
                          <TableCell className="hidden text-sm text-muted-foreground md:table-cell">
                            {pickup?.city ?? "—"} → {drop?.city ?? "—"}
                          </TableCell>
                          <TableCell className="hidden text-xs sm:table-cell">
                            {order.assigned_agent_id ? (
                              <span className="text-muted-foreground">Assigned</span>
                            ) : (
                              <span className="text-warning-foreground">Unassigned</span>
                            )}
                          </TableCell>
                          <TableCell className="text-sm font-medium">
                            {formatCurrency(order.total_charge)}
                          </TableCell>
                          <TableCell>
                            <StatusBadge status={order.status} />
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
              <PaginationBar
                offset={offset}
                limit={LIMIT}
                count={(data ?? []).length}
                onChange={setOffset}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
