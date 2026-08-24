import { createFileRoute } from "@tanstack/react-router";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Building2, Check, Edit2, Loader2, Plus, Search, Trash2, X } from "lucide-react";
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
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { adminApi } from "@/lib/api-client";

export const Route = createFileRoute("/admin/areas")({
  head: () => ({
    meta: [
      { title: "Service Areas — SwiftRoute Admin" },
      {
        name: "description",
        content:
          "Map postal codes to delivery zones so pickup and drop addresses resolve to the right rate card.",
      },
      { property: "og:title", content: "Service Areas — SwiftRoute Admin" },
      { property: "og:description", content: "Postal code to zone mapping for serviceability." },
    ],
  }),
  component: () => (
    <RoleGuard role="ADMIN">
      <AreasPage />
    </RoleGuard>
  ),
});

const LIMIT = 20;

function AreasPage() {
  const queryClient = useQueryClient();
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 250);
  const [name, setName] = useState("");
  const [postal, setPostal] = useState("");
  const [zoneId, setZoneId] = useState("");
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editPostal, setEditPostal] = useState("");

  const zonesQuery = useQuery({
    queryKey: ["admin", "zones", { limit: 100, offset: 0 }],
    queryFn: () => adminApi.listZones({ limit: 100, offset: 0 }),
    staleTime: 300_000,
  });

  const areasQuery = useQuery({
    queryKey: ["admin", "areas", { limit: LIMIT, offset }],
    queryFn: () => adminApi.listAreas({ limit: LIMIT, offset }),
    placeholderData: keepPreviousData,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["admin", "areas"] });

  const create = useMutation({
    mutationFn: () =>
      adminApi.createArea({
        name: name.trim(),
        postal_code: postal.trim(),
        zone_id: zoneId,
      }),
    onSuccess: async () => {
      toast.success("Area created");
      setName("");
      setPostal("");
      await invalidate();
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const toggle = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      adminApi.updateArea(id, { is_active }),
    onSuccess: async () => {
      toast.success("Area updated");
      await invalidate();
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const updateDetails = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      adminApi.updateArea(id, { name }),
    onSuccess: async () => {
      toast.success("Area updated");
      setEditingId(null);
      await invalidate();
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const changeZone = useMutation({
    mutationFn: ({ id, zone_id }: { id: string; zone_id: string }) =>
      adminApi.updateArea(id, { zone_id }),
    onSuccess: async () => {
      toast.success("Area moved to new zone");
      await invalidate();
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const remove = useMutation({
    mutationFn: (id: string) => adminApi.deleteArea(id),
    onSuccess: async () => {
      toast.success("Area deleted");
      setDeleteId(null);
      await invalidate();
    },
    onError: (err: Error) => {
      toast.error(err.message);
      setDeleteId(null);
    },
  });

  const zones = zonesQuery.data ?? [];
  const zoneName = (id: string) => zones.find((z) => z.id === id)?.name ?? id;

  const areas = useMemo(() => {
    const term = debouncedSearch.trim().toLowerCase();
    const list = areasQuery.data ?? [];
    if (!term) return list;
    return list.filter(
      (a) => a.name.toLowerCase().includes(term) || a.postal_code.includes(term),
    );
  }, [areasQuery.data, debouncedSearch]);

  return (
    <div className="space-y-6">
      <PageHeader title="Areas" description="Postal codes mapped to delivery zones." />

      <section className="card-surface p-4 sm:p-6">
        <h2 className="mb-4 text-base font-semibold">Add area</h2>
        <form
          className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_160px_minmax(0,1fr)_auto] sm:items-end"
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate();
          }}
        >
          <Field id="aname" label="Area name">
            <Input
              id="aname"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Andheri East"
              required
            />
          </Field>
          <Field id="apostal" label="Postal code">
            <Input
              id="apostal"
              value={postal}
              inputMode="numeric"
              onChange={(e) => setPostal(e.target.value)}
              placeholder="400069"
              required
            />
          </Field>
          <Field label="Zone">
            <Select value={zoneId} onValueChange={setZoneId} disabled={zonesQuery.isPending}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select zone" />
              </SelectTrigger>
              <SelectContent>
                {zones.map((z) => (
                  <SelectItem key={z.id} value={z.id}>
                    {z.name} ({z.code})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Button
            type="submit"
            disabled={!name.trim() || !postal.trim() || !zoneId || create.isPending}
          >
            {create.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Plus className="size-4" />
            )}
            Add
          </Button>
        </form>
        {zones.length === 0 && !zonesQuery.isPending ? (
          <p className="mt-3 text-sm text-muted-foreground">
            Create a zone first — areas must belong to a zone.
          </p>
        ) : null}
      </section>

      <section className="card-surface p-4 sm:p-6">
        <div className="relative mb-4">
          <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search area or postal code…"
            className="pl-9"
          />
        </div>

        {areasQuery.isError ? (
          <ErrorState error={areasQuery.error} onRetry={() => void areasQuery.refetch()} />
        ) : areasQuery.isPending ? (
          <LoadingRows rows={5} />
        ) : areas.length === 0 ? (
          <EmptyState
            title="No areas found"
            description="Add postal codes so addresses resolve to a zone."
            icon={<Building2 className="size-5" />}
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Area</TableHead>
                    <TableHead>Postal code</TableHead>
                    <TableHead>Zone</TableHead>
                    <TableHead>Active</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {areas.map((area) => (
                    <TableRow key={area.id}>
                      <TableCell>
                        {editingId === area.id ? (
                          <Input 
                            value={editName} 
                            onChange={(e) => setEditName(e.target.value)} 
                            className="h-8"
                          />
                        ) : (
                          <span className="font-medium">{area.name}</span>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {area.postal_code}
                      </TableCell>
                      <TableCell>
                        <Select
                          value={area.zone_id}
                          disabled={changeZone.isPending || zones.length === 0}
                          onValueChange={(v) => changeZone.mutate({ id: area.id, zone_id: v })}
                        >
                          <SelectTrigger className="h-8 w-44">
                            <SelectValue placeholder={zoneName(area.zone_id)} />
                          </SelectTrigger>
                          <SelectContent>
                            {zones.map((z) => (
                              <SelectItem key={z.id} value={z.id}>
                                {z.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell>
                        <Switch
                          checked={area.is_active}
                          disabled={toggle.isPending}
                          onCheckedChange={(checked) =>
                            toggle.mutate({ id: area.id, is_active: checked })
                          }
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        {editingId === area.id ? (
                          <>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => updateDetails.mutate({ id: area.id, name: editName })}
                              disabled={updateDetails.isPending}
                            >
                              <Check className="size-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => setEditingId(null)}
                            >
                              <X className="size-4" />
                            </Button>
                          </>
                        ) : (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => {
                              setEditingId(area.id);
                              setEditName(area.name);
                              setEditPostal(area.postal_code);
                            }}
                          >
                            <Edit2 className="size-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label={`Delete ${area.name}`}
                          onClick={() => setDeleteId(area.id)}
                        >
                          <Trash2 className="size-4 text-destructive" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <PaginationBar
              offset={offset}
              limit={LIMIT}
              count={(areasQuery.data ?? []).length}
              onChange={setOffset}
            />
          </>
        )}
      </section>

      <AlertDialog open={deleteId !== null} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this area?</AlertDialogTitle>
            <AlertDialogDescription>
              Addresses with this postal code will no longer be serviceable.
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
