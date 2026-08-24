import { cn } from "@/lib/utils";
import type { AvailabilityStatus, OrderStatus } from "@/lib/api-types";
import { titleCase } from "@/lib/format";

const STATUS_STYLES: Record<OrderStatus, string> = {
  CREATED: "bg-secondary text-secondary-foreground border-border",
  PICKED_UP: "bg-accent/10 text-accent border-accent/25",
  IN_TRANSIT: "bg-accent/10 text-accent border-accent/25",
  OUT_FOR_DELIVERY: "bg-warning/15 text-warning-foreground border-warning/40",
  DELIVERED: "bg-success/12 text-success border-success/30",
  FAILED: "bg-destructive/10 text-destructive border-destructive/25",
  CANCELLED: "bg-muted text-muted-foreground border-border",
};

export function StatusBadge({
  status,
  className,
}: {
  status: OrderStatus;
  className?: string | undefined;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        STATUS_STYLES[status] ?? STATUS_STYLES.CREATED,
        className,
      )}
    >
      <span className="size-1.5 rounded-full bg-current opacity-70" />
      {titleCase(status)}
    </span>
  );
}

const AVAILABILITY_STYLES: Record<AvailabilityStatus, string> = {
  AVAILABLE: "bg-success/12 text-success border-success/30",
  BUSY: "bg-warning/15 text-warning-foreground border-warning/40",
  OFFLINE: "bg-muted text-muted-foreground border-border",
};

export function AvailabilityBadge({ status }: { status: AvailabilityStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        AVAILABILITY_STYLES[status],
      )}
    >
      <span className="size-1.5 rounded-full bg-current" />
      {titleCase(status)}
    </span>
  );
}
