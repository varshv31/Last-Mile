import { createFileRoute } from "@tanstack/react-router";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { Boxes, Check, Loader2, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Field } from "@/components/address-fields";
import { RoleGuard } from "@/components/role-guard";
import {
  EmptyState,
  ErrorState,
  LoadingRows,
  PageHeader,
  PaginationBar,
} from "@/components/states";
import { adminApi } from "@/lib/api-client";
import type { OrderType, ZoneType } from "@/lib/api-types";
import { formatCurrency, formatDate, titleCase } from "@/lib/format";

export const Route = createFileRoute("/admin/rates")({
  head: () => ({
    meta: [
      { title: "Rate Cards — SwiftRoute Admin" },
      {
        name: "description",
        content:
          "Configure B2B and B2C weight-slab pricing for intra-zone and inter-zone last-mile deliveries.",
      },
      { property: "og:title", content: "Rate Cards — SwiftRoute Admin" },
      { property: "og:description", content: "B2B and B2C weight slab pricing." },
    ],
  }),
  component: () => (
    <RoleGuard role="ADMIN">
      <RatesPage />
    </RoleGuard>
  ),
});

const LIMIT = 20;

function RatesPage() {
  const queryClient = useQueryClient();
  const [offset, setOffset] = useState(0);
  const [orderType, setOrderType] = useState<OrderType>("B2C");
  const [zoneType, setZoneType] = useState<ZoneType>("INTRA_ZONE");
  const [minWeight, setMinWeight] = useState("");
  const [maxWeight, setMaxWeight] = useState("");
  const [price, setPrice] = useState("");
  const [effectiveFrom, setEffectiveFrom] = useState("");
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [editing, setEditing] = useState<Record<string, string>>({});

  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ["admin", "rates", { limit: LIMIT, offset }],
    queryFn: () => adminApi.listRates({ limit: LIMIT, offset }),
    placeholderData: keepPreviousData,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["admin", "rates"] });

  const create = useMutation({
    mutationFn: () =>
      adminApi.createRate({
        order_type: orderType,
        zone_type: zoneType,
        min_weight: Number(minWeight),
        max_weight: Number(maxWeight),
        price: Number(price),
        ...(effectiveFrom ? { effective_from: `${effectiveFrom}T00:00:00Z` } : {}),
      }),
    onSuccess: async () => {
      toast.success("Rate card created");
      setMinWeight("");
      setMaxWeight("");
      setPrice("");
      setEffectiveFrom("");
      await invalidate();
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const update = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string;
      body: { price?: number | undefined; is_active?: boolean | undefined };
    }) => adminApi.updateRate(id, body),
    onSuccess: async (_res, vars) => {
      toast.success("Rate card updated");
      setEditing((prev) => {
        const next = { ...prev };
        delete next[vars.id];
        return next;
      });
      await invalidate();
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const remove = useMutation({
    mutationFn: (id: string) => adminApi.deleteRate(id),
    onSuccess: async () => {
      toast.success("Rate card deleted");
      setDeleteId(null);
      await invalidate();
    },
    onError: (err: Error) => {
      toast.error(err.message);
      setDeleteId(null);
    },
  });

  const rates = data ?? [];
  const formValid =
    Number(maxWeight) > Number(minWeight) && minWeight !== "" && Number(price) >= 0 && price !== "";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Rate cards"
        description="Weight-slab pricing per order type and zone type."
      />

      <section className="card-surface p-4 sm:p-6">
        <h2 className="mb-4 text-base font-semibold">Add rate card</h2>
        <form
          className="grid gap-4 sm:grid-cols-3 lg:grid-cols-6 lg:items-end"
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate();
          }}
        >
          <Field label="Order type">
            <Select value={orderType} onValueChange={(v) => setOrderType(v as OrderType)}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="B2C">B2C</SelectItem>
                <SelectItem value="B2B">B2B</SelectItem>
              </SelectContent>
            </Select>
          </Field>
          <Field label="Zone type">
            <Select value={zoneType} onValueChange={(v) => setZoneType(v as ZoneType)}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="INTRA_ZONE">Intra zone</SelectItem>
                <SelectItem value="INTER_ZONE">Inter zone</SelectItem>
              </SelectContent>
            </Select>
          </Field>
          <Field id="minw" label="Min weight (kg)">
            <Input
              id="minw"
              type="number"
              min="0"
              step="0.01"
              value={minWeight}
              onChange={(e) => setMinWeight(e.target.value)}
              required
            />
          </Field>
          <Field id="maxw" label="Max weight (kg)">
            <Input
              id="maxw"
              type="number"
              min="0"
              step="0.01"
              value={maxWeight}
              onChange={(e) => setMaxWeight(e.target.value)}
              required
            />
          </Field>
          <Field id="price" label="Price (₹)">
            <Input
              id="price"
              type="number"
              min="0"
              step="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              required
            />
          </Field>
          <div className="grid gap-4 sm:col-span-3 lg:col-span-1">
            <Field id="eff" label="Effective from">
              <Input
                id="eff"
                type="date"
                value={effectiveFrom}
                onChange={(e) => setEffectiveFrom(e.target.value)}
              />
            </Field>
          </div>
          <div className="sm:col-span-3 lg:col-span-6">
            <Button type="submit" disabled={!formValid || create.isPending}>
              {create.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Plus className="size-4" />
              )}
              Add rate card
            </Button>
          </div>
        </form>
      </section>

      <section className="card-surface p-4 sm:p-6">
        {isError ? (
          <ErrorState error={error} onRetry={() => void refetch()} />
        ) : isPending ? (
          <LoadingRows rows={5} />
        ) : rates.length === 0 ? (
          <EmptyState
            title="No rate cards"
            description="Charges cannot be calculated until at least one rate card exists."
            icon={<Boxes className="size-5" />}
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Weight slab</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead className="hidden md:table-cell">Effective</TableHead>
                    <TableHead>Active</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rates.map((rate) => {
                    const draft = editing[rate.id];
                    return (
                      <TableRow key={rate.id}>
                        <TableCell>
                          <span className="font-medium">{rate.order_type}</span>
                          <span className="block text-xs text-muted-foreground">
                            {titleCase(rate.zone_type)}
                          </span>
                        </TableCell>
                        <TableCell className="text-sm">
                          {rate.min_weight} – {rate.max_weight} kg
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Input
                              className="h-8 w-24"
                              type="number"
                              min="0"
                              step="0.01"
                              value={draft ?? String(rate.price)}
                              onChange={(e) =>
                                setEditing((prev) => ({ ...prev, [rate.id]: e.target.value }))
                              }
                            />
                            {draft !== undefined && Number(draft) !== rate.price ? (
                              <Button
                                size="icon"
                                className="size-8"
                                aria-label="Save price"
                                disabled={update.isPending}
                                onClick={() =>
                                  update.mutate({ id: rate.id, body: { price: Number(draft) } })
                                }
                              >
                                <Check className="size-4" />
                              </Button>
                            ) : (
                              <span className="text-xs text-muted-foreground">
                                {formatCurrency(rate.price)}
                              </span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="hidden text-xs text-muted-foreground md:table-cell">
                          {rate.effective_from ? formatDate(rate.effective_from) : "—"} →{" "}
                          {rate.effective_to ? formatDate(rate.effective_to) : "open"}
                        </TableCell>
                        <TableCell>
                          <Switch
                            checked={rate.is_active}
                            disabled={update.isPending}
                            onCheckedChange={(checked) =>
                              update.mutate({ id: rate.id, body: { is_active: checked } })
                            }
                          />
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            aria-label="Delete rate card"
                            onClick={() => setDeleteId(rate.id)}
                          >
                            <Trash2 className="size-4 text-destructive" />
                          </Button>
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
              count={rates.length}
              onChange={setOffset}
            />
          </>
        )}
      </section>

      <AlertDialog open={deleteId !== null} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this rate card?</AlertDialogTitle>
            <AlertDialogDescription>
              Orders in this weight slab will fail to price until another card covers it.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => deleteId && remove.mutate(deleteId)}>
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
