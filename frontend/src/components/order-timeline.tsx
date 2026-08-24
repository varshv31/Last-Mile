import { Check, CircleDot } from "lucide-react";
import type { TrackingEvent } from "@/lib/api-types";
import { formatDateTime, relativeTime, titleCase } from "@/lib/format";
import { cn } from "@/lib/utils";

export function OrderTimeline({ events }: { events: TrackingEvent[] }) {
  if (!events.length) {
    return <p className="text-sm text-muted-foreground">No tracking events yet.</p>;
  }
  const ordered = [...events].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  );

  return (
    <ol className="relative space-y-6 pl-7">
      <span className="absolute top-1 bottom-1 left-[11px] w-px bg-border" aria-hidden />
      {ordered.map((event, index) => {
        const isLast = index === ordered.length - 1;
        const negative = event.new_status === "FAILED" || event.new_status === "CANCELLED";
        return (
          <li key={event.id} className="relative animate-in fade-in slide-in-from-bottom-1">
            <span
              className={cn(
                "absolute top-0.5 -left-7 flex size-[23px] items-center justify-center rounded-full border-2 bg-card",
                negative
                  ? "border-destructive text-destructive"
                  : isLast
                    ? "border-accent text-accent"
                    : "border-success text-success",
              )}
            >
              {isLast && !negative ? (
                <CircleDot className="size-3" />
              ) : (
                <Check className="size-3" />
              )}
            </span>
            <div className="flex flex-wrap items-baseline gap-x-2">
              <p className="text-sm font-semibold text-foreground">
                {titleCase(event.new_status)}
              </p>
              <span className="text-xs text-muted-foreground">
                {relativeTime(event.created_at)}
              </span>
            </div>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {formatDateTime(event.created_at)}
              {event.actor_name
                ? ` · ${event.actor_name}${event.actor_role ? ` (${titleCase(event.actor_role)})` : ""}`
                : event.actor_role
                  ? ` · ${titleCase(event.actor_role)}`
                  : ""}
            </p>
            {event.remarks ? (
              <p className="mt-2 rounded-lg bg-secondary px-3 py-2 text-sm text-foreground/85">
                {event.remarks}
              </p>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}
