import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { Calculator, Loader2, PackagePlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AddressFields, EMPTY_ADDRESS, Field, addressComplete } from "@/components/address-fields";
import { QuoteBreakdown } from "@/components/charge-breakdown";
import { RoleGuard } from "@/components/role-guard";
import { ErrorState, PageHeader } from "@/components/states";
import { customerApi } from "@/lib/api-client";
import type {
  AddressInput,
  OrderType,
  PackageInput,
  PaymentType,
  RateQuote,
} from "@/lib/api-types";

export const Route = createFileRoute("/orders/new")({
  head: () => ({
    meta: [
      { title: "Create Shipment — SwiftRoute" },
      {
        name: "description",
        content:
          "Create a new last-mile delivery order and preview the exact billable weight and charges before you confirm.",
      },
      { property: "og:title", content: "Create Shipment — SwiftRoute" },
      {
        property: "og:description",
        content: "Enter pickup and drop details, preview charges, then place your delivery order.",
      },
    ],
  }),
  component: () => (
    <RoleGuard role="CUSTOMER">
      <NewOrder />
    </RoleGuard>
  ),
});

const EMPTY_PACKAGE = { length_cm: "", breadth_cm: "", height_cm: "", actual_weight_kg: "" };

function NewOrder() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [pickup, setPickup] = useState<AddressInput>({ ...EMPTY_ADDRESS });
  const [drop, setDrop] = useState<AddressInput>({ ...EMPTY_ADDRESS });
  const [pkg, setPkg] = useState({ ...EMPTY_PACKAGE });
  const [orderType, setOrderType] = useState<OrderType>("B2C");
  const [paymentType, setPaymentType] = useState<PaymentType>("PREPAID");
  const [quote, setQuote] = useState<RateQuote | null>(null);

  const packageValid =
    Number(pkg.length_cm) > 0 &&
    Number(pkg.breadth_cm) > 0 &&
    Number(pkg.height_cm) > 0 &&
    Number(pkg.actual_weight_kg) > 0;

  const formValid = addressComplete(pickup) && addressComplete(drop) && packageValid;

  const buildPayload = () => {
    const packagePayload: PackageInput = {
      length_cm: Number(pkg.length_cm),
      breadth_cm: Number(pkg.breadth_cm),
      height_cm: Number(pkg.height_cm),
      actual_weight_kg: Number(pkg.actual_weight_kg),
    };
    return {
      pickup_address: pickup,
      drop_address: drop,
      package: packagePayload,
      order_type: orderType,
      payment_type: paymentType,
    };
  };

  const calculate = useMutation({
    mutationFn: () => customerApi.calculate(buildPayload()),
    onSuccess: (data) => {
      setQuote(data);
      toast.success("Charges calculated");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const create = useMutation({
    mutationFn: () => customerApi.createOrder(buildPayload()),
    onSuccess: async (order) => {
      toast.success(`Order ${order.order_number} created`);
      await queryClient.invalidateQueries({ queryKey: ["customer", "orders"] });
      void navigate({ to: "/orders/$orderId", params: { orderId: order.id } });
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const busy = calculate.isPending || create.isPending;

  return (
    <div className="space-y-6">
      <PageHeader
        title="New shipment"
        description="Enter shipment details, preview the charge, then confirm."
      />

      <form
        className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]"
        onSubmit={(e) => {
          e.preventDefault();
          if (!formValid) {
            toast.error("Fill in all pickup, drop and package details.");
            return;
          }
          create.mutate();
        }}
      >
        <div className="space-y-6">
          <section className="card-surface p-4 sm:p-6">
            <h2 className="mb-4 text-base font-semibold">Pickup address</h2>
            <AddressFields idPrefix="pickup" value={pickup} onChange={setPickup} disabled={busy} />
          </section>

          <section className="card-surface p-4 sm:p-6">
            <h2 className="mb-4 text-base font-semibold">Drop address</h2>
            <AddressFields idPrefix="drop" value={drop} onChange={setDrop} disabled={busy} />
          </section>

          <section className="card-surface p-4 sm:p-6">
            <h2 className="mb-4 text-base font-semibold">Package &amp; billing</h2>
            <div className="grid gap-4 sm:grid-cols-4">
              <Field id="len" label="Length (cm)">
                <Input
                  id="len"
                  type="number"
                  min="0"
                  step="0.1"
                  value={pkg.length_cm}
                  disabled={busy}
                  onChange={(e) => setPkg({ ...pkg, length_cm: e.target.value })}
                />
              </Field>
              <Field id="bre" label="Breadth (cm)">
                <Input
                  id="bre"
                  type="number"
                  min="0"
                  step="0.1"
                  value={pkg.breadth_cm}
                  disabled={busy}
                  onChange={(e) => setPkg({ ...pkg, breadth_cm: e.target.value })}
                />
              </Field>
              <Field id="hei" label="Height (cm)">
                <Input
                  id="hei"
                  type="number"
                  min="0"
                  step="0.1"
                  value={pkg.height_cm}
                  disabled={busy}
                  onChange={(e) => setPkg({ ...pkg, height_cm: e.target.value })}
                />
              </Field>
              <Field id="wt" label="Weight (kg)">
                <Input
                  id="wt"
                  type="number"
                  min="0"
                  step="0.01"
                  value={pkg.actual_weight_kg}
                  disabled={busy}
                  onChange={(e) => setPkg({ ...pkg, actual_weight_kg: e.target.value })}
                />
              </Field>
              <Field label="Order type" className="sm:col-span-2">
                <Select
                  value={orderType}
                  onValueChange={(v) => setOrderType(v as OrderType)}
                  disabled={busy}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="B2C">B2C — Business to consumer</SelectItem>
                    <SelectItem value="B2B">B2B — Business to business</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Payment type" className="sm:col-span-2">
                <Select
                  value={paymentType}
                  onValueChange={(v) => setPaymentType(v as PaymentType)}
                  disabled={busy}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PREPAID">Prepaid</SelectItem>
                    <SelectItem value="COD">Cash on delivery</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
            </div>
          </section>
        </div>

        <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
          <div className="card-surface p-4 sm:p-5">
            <h2 className="text-base font-semibold">Charge preview</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Pricing is calculated by the server from your zones and rate cards.
            </p>

            <Button
              type="button"
              variant="outline"
              className="mt-4 w-full"
              disabled={!formValid || busy}
              onClick={() => calculate.mutate()}
            >
              {calculate.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Calculator className="size-4" />
              )}
              Calculate charges
            </Button>

            <div className="mt-5">
              {calculate.isError ? (
                <ErrorState error={calculate.error} />
              ) : quote ? (
                <QuoteBreakdown quote={quote} />
              ) : (
                <p className="rounded-lg border border-dashed border-border px-4 py-6 text-center text-sm text-muted-foreground">
                  Fill the form and calculate to see the breakdown.
                </p>
              )}
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={!formValid || busy}>
            {create.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <PackagePlus className="size-4" />
            )}
            Create order
          </Button>
          <p className="text-center text-xs text-muted-foreground">
            The final charge is recalculated server-side on creation.
          </p>
        </aside>
      </form>
    </div>
  );
}
