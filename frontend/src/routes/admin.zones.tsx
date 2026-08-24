import { createFileRoute } from "@tanstack/react-router";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { Check, Edit2, Loader2, Map, Plus, Trash2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
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
import { formatDate } from "@/lib/format";

export const Route = createFileRoute("/admin/zones")({
  head: () => ({
    meta: [
      { title: "Delivery Zones — SwiftRoute Admin" },
      {
        name: "description",
        content:
          "Create and manage the delivery zones that drive intra-zone and inter-zone pricing across the network.",
      },
      { property: "og:title", content: "Delivery Zones — SwiftRoute Admin" },
      { property: "og:description", content: "Manage the zones your pricing is built on." },
    ],
  }),
  component: () => (
    <RoleGuard role="ADMIN">
      <ZonesPage />
    </RoleGuard>
  ),
});

const LIMIT = 20;

function ZonesPage() {
  const queryClient = useQueryClient();
  const [offset, setOffset] = useState(0);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [description, setDescription] = useState("");
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");

  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ["admin", "zones", { limit: LIMIT, offset }],
    queryFn: () => adminApi.listZones({ limit: LIMIT, offset }),
    placeholderData: keepPreviousData,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["admin", "zones"] });

  const create = useMutation({
    mutationFn: () =>
      adminApi.createZone({
        name: name.trim(),
        code: code.trim().toUpperCase(),
        ...(description.trim() ? { description: description.trim() } : {}),
      }),
    onSuccess: async () => {
      toast.success("Zone created");
      setName("");
      setCode("");
      setDescription("");
      await invalidate();
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const toggle = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      adminApi.updateZone(id, { is_active }),
    onSuccess: async () => {
      toast.success("Zone updated");
      await invalidate();
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const updateDetails = useMutation({
    mutationFn: ({ id, name, description }: { id: string; name: string; description: string }) =>
      adminApi.updateZone(id, { name, description }),
    onSuccess: async () => {
      toast.success("Zone updated");
      setEditingId(null);
      await invalidate();
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const remove = useMutation({
    mutationFn: (id: string) => adminApi.deleteZone(id),
    onSuccess: async () => {
      toast.success("Zone deleted");
      setDeleteId(null);
      await invalidate();
    },
    onError: (err: Error) => {
      toast.error(err.message);
      setDeleteId(null);
    },
  });

  const zones = data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader title="Zones" description="Service zones used for pricing and routing." />

      <section className="card-surface p-4 sm:p-6">
        <h2 className="mb-4 text-base font-semibold">Add zone</h2>
        <form
          className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_140px_minmax(0,1fr)_auto] sm:items-end"
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate();
          }}
        >
          <Field id="zname" label="Name">
            <Input
              id="zname"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Mumbai North"
              required
            />
          </Field>
          <Field id="zcode" label="Code">
            <Input
              id="zcode"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="MUM-N"
              required
            />
          </Field>
          <Field id="zdesc" label="Description (optional)">
            <Input
              id="zdesc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Northern suburbs"
            />
          </Field>
          <Button type="submit" disabled={!name.trim() || !code.trim() || create.isPending}>
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
          <LoadingRows rows={5} />
        ) : zones.length === 0 ? (
          <EmptyState
            title="No zones yet"
            description="Add your first zone to start configuring rates."
            icon={<Map className="size-5" />}
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Zone</TableHead>
                    <TableHead className="hidden md:table-cell">Description</TableHead>
                    <TableHead className="hidden sm:table-cell">Created</TableHead>
                    <TableHead>Active</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {zones.map((zone) => (
                    <TableRow key={zone.id}>
                      <TableCell>
                        {editingId === zone.id ? (
                          <Input 
                            value={editName} 
                            onChange={(e) => setEditName(e.target.value)} 
                            className="h-8"
                          />
                        ) : (
                          <>
                            <span className="font-medium">{zone.name}</span>
                            <span className="block text-xs text-muted-foreground">{zone.code}</span>
                          </>
                        )}
                      </TableCell>
                      <TableCell className="hidden text-sm text-muted-foreground md:table-cell">
                        {editingId === zone.id ? (
                          <Input 
                            value={editDesc} 
                            onChange={(e) => setEditDesc(e.target.value)} 
                            className="h-8"
                          />
                        ) : (
                          zone.description ?? "—"
                        )}
                      </TableCell>
                      <TableCell className="hidden text-sm text-muted-foreground sm:table-cell">
                        {formatDate(zone.created_at)}
                      </TableCell>
                      <TableCell>
                        <Switch
                          checked={zone.is_active}
                          disabled={toggle.isPending}
                          onCheckedChange={(checked) =>
                            toggle.mutate({ id: zone.id, is_active: checked })
                          }
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        {editingId === zone.id ? (
                          <>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => updateDetails.mutate({ id: zone.id, name: editName, description: editDesc })}
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
                              setEditingId(zone.id);
                              setEditName(zone.name);
                              setEditDesc(zone.description ?? "");
                            }}
                          >
                            <Edit2 className="size-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label={`Delete ${zone.name}`}
                          onClick={() => setDeleteId(zone.id)}
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
              count={zones.length}
              onChange={setOffset}
            />
          </>
        )}
      </section>

      <AlertDialog open={deleteId !== null} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this zone?</AlertDialogTitle>
            <AlertDialogDescription>
              Zones in use by areas or orders may not be deletable.
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
