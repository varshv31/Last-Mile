import { createFileRoute } from "@tanstack/react-router";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { ClipboardList } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RoleGuard } from "@/components/role-guard";
import {
  EmptyState,
  ErrorState,
  LoadingRows,
  PageHeader,
  PaginationBar,
} from "@/components/states";
import { AgentOrderList } from "@/routes/agent.index";
import { agentApi } from "@/lib/api-client";
import { ORDER_STATUSES, type OrderStatus } from "@/lib/api-types";
import { titleCase } from "@/lib/format";

export const Route = createFileRoute("/agent/history")({
  head: () => ({
    meta: [
      { title: "Delivery History — SwiftRoute Agent" },
      {
        name: "description",
        content: "Review every delivery order that has been assigned to you, filtered by status.",
      },
      { property: "og:title", content: "Delivery History — SwiftRoute Agent" },
      { property: "og:description", content: "Your completed and past delivery assignments." },
    ],
  }),
  component: () => (
    <RoleGuard role="AGENT">
      <AgentHistory />
    </RoleGuard>
  ),
});

const LIMIT = 20;

function AgentHistory() {
  const [offset, setOffset] = useState(0);
  const [status, setStatus] = useState<OrderStatus | "ALL">("ALL");

  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ["agent", "orders", { limit: LIMIT, offset }],
    queryFn: () => agentApi.listOrders({ limit: LIMIT, offset }),
    placeholderData: keepPreviousData,
    staleTime: 20_000,
  });

  const orders = useMemo(
    () => (data ?? []).filter((o) => status === "ALL" || o.status === status),
    [data, status],
  );

  return (
    <div className="space-y-6">
      <PageHeader title="History" description="All orders assigned to you." />

      <section className="card-surface p-4 sm:p-6">
        <div className="mb-4 flex justify-end">
          <Select value={status} onValueChange={(v) => setStatus(v as OrderStatus | "ALL")}>
            <SelectTrigger className="w-full sm:w-56">
              <SelectValue placeholder="Filter status" />
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
          <LoadingRows rows={5} />
        ) : orders.length === 0 ? (
          <EmptyState
            title="Nothing here yet"
            description="Assigned deliveries will show up in this list."
            icon={<ClipboardList className="size-5" />}
          />
        ) : (
          <>
            <AgentOrderList orders={orders} />
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
