import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { BadgeIndianRupee, Check, Loader2, Plus, Trash2 } from "lucide-react";
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
import { EmptyState, ErrorState, LoadingRows, PageHeader } from "@/components/states";
import { adminApi } from "@/lib/api-client";
import type { OrderType, SurchargeType } from "@/lib/api-types";
import { formatCurrency } from "@/lib/format";

export const Route = createFileRoute("/admin/cod-surcharges")({
  head: () => ({
    meta: [
      { title: "COD Surcharges — SwiftRoute Admin" },
      {
        name: "description",
        content:
          "Set fixed or percentage cash-on-delivery surcharges applied to B2B and B2C orders at checkout.",
      },
      { property: "og:title", content: "COD Surcharges — SwiftRoute Admin" },
      { property: "og:description", content: "Fixed or percentage cash-on-delivery fees." },
    ],
  }),
  component: () => (
    <RoleGuard role="ADMIN">
      <CodSurchargesPage />
    </RoleGuard>
  ),
});

function CodSurchargesPage() {
  const queryClient = useQueryClient();
  const [orderType, setOrderType] = useState<OrderType>("B2C");
  const [surchargeType, setSurchargeType] = useState<SurchargeType>("FIXED");
  const [value, setValue] = useState("");
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [editing, setEditing] = useState<Record<string, string>>({});

  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ["admin", "cod-surcharges"],
    queryFn: () => adminApi.listCodSurcharges(),
  });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["admin", "cod-surcharges"] });

  const create = useMutation({
    mutationFn: () =>
      adminApi.createCodSurcharge({
        order_type: orderType,
        surcharge_type: surchargeType,
        value: Number(value),
      }),
    onSuccess: async () => {
      toast.success("COD surcharge created");
      setValue("");
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
      body: {
        value?: number | undefined;
        is_active?: boolean | undefined;
        surcharge_type?: SurchargeType | undefined;
      };
    }) => adminApi.updateCodSurcharge(id, body),
    onSuccess: async (_res, vars) => {
      toast.success("COD surcharge updated");
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
    mutationFn: (id: string) => adminApi.deleteCodSurcharge(id),
    onSuccess: async () => {
      toast.success("COD surcharge deleted");
      setDeleteId(null);
      await invalidate();
    },
    onError: (err: Error) => {
      toast.error(err.message);
      setDeleteId(null);
    },
  });

  const surcharges = data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="COD surcharges"
        description="Extra fee applied to cash-on-delivery orders."
      />

      <section className="card-surface p-4 sm:p-6">
        <h2 className="mb-4 text-base font-semibold">Add surcharge</h2>
        <form
          className="grid gap-4 sm:grid-cols-[180px_180px_minmax(0,1fr)_auto] sm:items-end"
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
          <Field label="Surcharge type">
            <Select
              value={surchargeType}
              onValueChange={(v) => setSurchargeType(v as SurchargeType)}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="FIXED">Fixed (₹)</SelectItem>
                <SelectItem value="PERCENTAGE">Percentage (%)</SelectItem>
              </SelectContent>
            </Select>
          </Field>
          <Field id="codvalue" label={surchargeType === "FIXED" ? "Amount (₹)" : "Percent (%)"}>
            <Input
              id="codvalue"
              type="number"
              min="0"
              step="0.01"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              required
            />
          </Field>
          <Button type="submit" disabled={value === "" || create.isPending}>
            {create.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Plus className="size-4" />
            )}
            Add
          </Button>
        </form>
      </section>

      <section className="card-surface p-4 sm:p-6">
        {isError ? (
          <ErrorState error={error} onRetry={() => void refetch()} />
        ) : isPending ? (
          <LoadingRows rows={3} />
        ) : surcharges.length === 0 ? (
          <EmptyState
            title="No COD surcharges"
            description="COD orders will be charged no extra fee until one is configured."
            icon={<BadgeIndianRupee className="size-5" />}
          />
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Order type</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Value</TableHead>
                  <TableHead>Active</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {surcharges.map((item) => {
                  const draft = editing[item.id];
                  return (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">{item.order_type}</TableCell>
                      <TableCell>
                        <Select
                          value={item.surcharge_type}
                          disabled={update.isPending}
                          onValueChange={(v) =>
                            update.mutate({
                              id: item.id,
                              body: { surcharge_type: v as SurchargeType },
                            })
                          }
                        >
                          <SelectTrigger className="h-8 w-36">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="FIXED">Fixed</SelectItem>
                            <SelectItem value="PERCENTAGE">Percentage</SelectItem>
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Input
                            className="h-8 w-24"
                            type="number"
                            min="0"
                            step="0.01"
                            value={draft ?? String(item.value)}
                            onChange={(e) =>
                              setEditing((prev) => ({ ...prev, [item.id]: e.target.value }))
                            }
                          />
                          {draft !== undefined && Number(draft) !== item.value ? (
                            <Button
                              size="icon"
                              className="size-8"
                              aria-label="Save value"
                              disabled={update.isPending}
                              onClick={() =>
                                update.mutate({ id: item.id, body: { value: Number(draft) } })
                              }
                            >
                              <Check className="size-4" />
                            </Button>
                          ) : (
                            <span className="text-xs text-muted-foreground">
                              {item.surcharge_type === "FIXED"
                                ? formatCurrency(item.value)
                                : `${item.value}%`}
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Switch
                          checked={item.is_active}
                          disabled={update.isPending}
                          onCheckedChange={(checked) =>
                            update.mutate({ id: item.id, body: { is_active: checked } })
                          }
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Delete surcharge"
                          onClick={() => setDeleteId(item.id)}
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
        )}
      </section>

      <AlertDialog open={deleteId !== null} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this surcharge?</AlertDialogTitle>
            <AlertDialogDescription>
              COD orders of this type will no longer carry an extra fee.
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
