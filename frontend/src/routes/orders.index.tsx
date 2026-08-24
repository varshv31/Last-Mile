import { createFileRoute, Link } from "@tanstack/react-router";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { PackagePlus, Search } from "lucide-react";
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
import { customerApi } from "@/lib/api-client";
import { ORDER_STATUSES, type OrderStatus } from "@/lib/api-types";
import { formatCurrency, formatDateTime, titleCase } from "@/lib/format";

export const Route = createFileRoute("/orders/")({
  head: () => ({
    meta: [
      { title: "My Orders — SwiftRoute" },
      {
        name: "description",
        content: "Browse, search and track every delivery order you have created with SwiftRoute.",
      },
      { property: "og:title", content: "My Orders — SwiftRoute" },
      { property: "og:description", content: "All of your last-mile shipments in one list." },
    ],
  }),
  component: () => (
    <RoleGuard role="CUSTOMER">
      <CustomerOrders />
    </RoleGuard>
  ),
});

const LIMIT = 20;

function CustomerOrders() {
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<OrderStatus | "ALL">("ALL");
  const debouncedSearch = useDebouncedValue(search, 300);

  const { data, isPending, isFetching, isError, error, refetch } = useQuery({
    queryKey: ["customer", "orders", { limit: LIMIT, offset }],
    queryFn: () => customerApi.listOrders({ limit: LIMIT, offset }),
    placeholderData: keepPreviousData,
    staleTime: 20_000,
  });

  const orders = useMemo(() => {
    const list = data ?? [];
    const term = debouncedSearch.trim().toLowerCase();
    return list.filter((o) => {
      if (status !== "ALL" && o.status !== status) return false;
      if (!term) return true;
      return (
        o.order_number.toLowerCase().includes(term) ||
        o.addresses.some(
          (a) =>
            a.city.toLowerCase().includes(term) ||
            a.postal_code.toLowerCase().includes(term) ||
            a.name.toLowerCase().includes(term),
        )
      );
    });
  }, [data, debouncedSearch, status]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Orders"
        description="Search and track all your shipments."
        actions={
          <Button asChild>
            <Link to="/orders/new">
              <PackagePlus className="size-4" />
              New shipment
            </Link>
          </Button>
        }
      />

      <div className="card-surface p-4 sm:p-6">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search order number, city, postal code…"
              className="pl-9"
            />
          </div>
          <Select value={status} onValueChange={(v) => setStatus(v as OrderStatus | "ALL")}>
            <SelectTrigger className="sm:w-52">
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All statuses</SelectItem>
              {ORDER_STATUSES.map((s) => (
                <SelectItem key={s} value={s}>
                  {titleCase(s)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {isError ? (
          <ErrorState error={error} onRetry={() => void refetch()} />
        ) : isPending ? (
          <LoadingRows rows={6} />
        ) : orders.length === 0 ? (
          <EmptyState
            title="No orders found"
            description={
              search || status !== "ALL"
                ? "Try adjusting your search or filters."
                : "Create your first shipment to get started."
            }
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Order</TableHead>
                    <TableHead className="hidden md:table-cell">Route</TableHead>
                    <TableHead className="hidden sm:table-cell">Type</TableHead>
                    <TableHead>Charge</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className={isFetching ? "opacity-60 transition-opacity" : undefined}>
                  {orders.map((order) => {
                    const pickup = order.addresses.find((a) => a.address_type === "PICKUP");
                    const drop = order.addresses.find((a) => a.address_type === "DROP");
                    return (
                      <TableRow key={order.id} className="cursor-pointer">
                        <TableCell>
                          <Link
                            to="/orders/$orderId"
                            params={{ orderId: order.id }}
                            className="block"
                          >
                            <span className="font-medium text-foreground">
                              {order.order_number}
                            </span>
                            <span className="block text-xs text-muted-foreground">
                              {formatDateTime(order.created_at)}
                            </span>
                          </Link>
                        </TableCell>
                        <TableCell className="hidden text-sm text-muted-foreground md:table-cell">
                          {pickup?.city ?? "—"} → {drop?.city ?? "—"}
                        </TableCell>
                        <TableCell className="hidden text-sm sm:table-cell">
                          {order.order_type} · {order.payment_type}
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
  );
}
