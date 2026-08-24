import { ArrowRight, Package, Receipt } from "lucide-react";
import type { OrderResponse, RateQuote } from "@/lib/api-types";
import { formatCurrency, formatWeight, titleCase } from "@/lib/format";
import { Badge } from "@/components/ui/badge";

function Row({
  label,
  value,
  emphasis,
}: {
  label: string;
  value: string;
  emphasis?: boolean;
}) {
  return (
    <div
      className={
        emphasis
          ? "flex items-center justify-between border-t border-border pt-3 text-base font-semibold"
          : "flex items-center justify-between text-sm"
      }
    >
      <span className={emphasis ? "text-foreground" : "text-muted-foreground"}>{label}</span>
      <span className={emphasis ? "text-foreground" : "font-medium text-foreground"}>{value}</span>
    </div>
  );
}

export function QuoteBreakdown({ quote }: { quote: RateQuote }) {
  return (
    <div className="space-y-5">
      <div className="rounded-lg border border-border bg-secondary/50 p-4">
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <div>
            <p className="font-medium text-foreground">{quote.pickup_area_name}</p>
            <p className="text-xs text-muted-foreground">
              {quote.pickup_zone_name} · {quote.pickup_postal_code}
            </p>
          </div>
          <ArrowRight className="mx-2 size-4 text-muted-foreground" />
          <div>
            <p className="font-medium text-foreground">{quote.drop_area_name}</p>
            <p className="text-xs text-muted-foreground">
              {quote.drop_zone_name} · {quote.drop_postal_code}
            </p>
          </div>
          <Badge variant="secondary" className="ml-auto">
            {titleCase(quote.zone_type)}
          </Badge>
        </div>
      </div>

      <div className="space-y-2.5">
        <p className="flex items-center gap-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          <Package className="size-3.5" /> Weight
        </p>
        <Row label="Actual weight" value={formatWeight(quote.actual_weight)} />
        <Row label="Volumetric weight (L×B×H / 5000)" value={formatWeight(quote.volumetric_weight)} />
        <Row label="Billable weight" value={formatWeight(quote.billable_weight)} />
      </div>

      <div className="space-y-2.5">
        <p className="flex items-center gap-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          <Receipt className="size-3.5" /> Charges
        </p>
        <Row label={`Base charge (${quote.order_type})`} value={formatCurrency(quote.base_charge)} />
        <Row
          label={quote.payment_type === "COD" ? "COD surcharge" : "COD surcharge (prepaid)"}
          value={formatCurrency(quote.cod_surcharge)}
        />
        <Row label="Total payable" value={formatCurrency(quote.total_charge)} emphasis />
      </div>
    </div>
  );
}

export function OrderChargeBreakdown({ order }: { order: OrderResponse }) {
  return (
    <div className="space-y-2.5">
      <Row label="Actual weight" value={formatWeight(order.actual_weight)} />
      <Row label="Volumetric weight" value={formatWeight(order.volumetric_weight)} />
      <Row label="Billable weight" value={formatWeight(order.billable_weight)} />
      <Row label="Base charge" value={formatCurrency(order.base_charge)} />
      <Row label="COD charge" value={formatCurrency(order.cod_charge)} />
      <Row label="Total charge" value={formatCurrency(order.total_charge)} emphasis />
    </div>
  );
}
