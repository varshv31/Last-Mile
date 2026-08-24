import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { useState, type ReactNode } from "react";
import {
  Boxes,
  Building2,
  ClipboardList,
  Coins,
  LayoutDashboard,
  LogOut,
  Map,
  Menu,
  Package,
  PackagePlus,
  Truck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useAuth } from "@/lib/auth";
import type { UserRole } from "@/lib/api-types";
import { cn } from "@/lib/utils";

interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
}

const NAV: Record<UserRole, NavItem[]> = {
  CUSTOMER: [
    { to: "/dashboard", label: "Dashboard", icon: <LayoutDashboard className="size-4" /> },
    { to: "/orders", label: "My Orders", icon: <Package className="size-4" /> },
    { to: "/orders/new", label: "New Shipment", icon: <PackagePlus className="size-4" /> },
  ],
  AGENT: [
    { to: "/agent", label: "My Deliveries", icon: <Truck className="size-4" /> },
    { to: "/agent/history", label: "History", icon: <ClipboardList className="size-4" /> },
  ],
  ADMIN: [
    { to: "/admin", label: "Overview", icon: <LayoutDashboard className="size-4" /> },
    { to: "/admin/orders", label: "Orders", icon: <Package className="size-4" /> },
    { to: "/admin/zones", label: "Zones", icon: <Map className="size-4" /> },
    { to: "/admin/areas", label: "Areas", icon: <Building2 className="size-4" /> },
    { to: "/admin/rates", label: "Rate Cards", icon: <Boxes className="size-4" /> },
    { to: "/admin/cod-surcharges", label: "COD Surcharges", icon: <Coins className="size-4" /> },
  ],
};

const ROLE_LABEL: Record<UserRole, string> = {
  CUSTOMER: "Customer",
  AGENT: "Delivery Agent",
  ADMIN: "Administrator",
};

function Brand({ compact }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="flex size-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
        <Truck className="size-5" />
      </div>
      {!compact ? (
        <div className="leading-tight">
          <p className="text-sm font-semibold text-sidebar-foreground">SwiftRoute</p>
          <p className="text-[11px] text-sidebar-foreground/60">Last-Mile Delivery</p>
        </div>
      ) : null}
    </div>
  );
}

function NavLinks({ items, onNavigate }: { items: NavItem[]; onNavigate?: () => void }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (
    <nav className="space-y-1">
      {items.map((item) => {
        const active =
          pathname === item.to ||
          (item.to !== "/admin" && item.to !== "/agent" && pathname.startsWith(`${item.to}/`));
        return (
          <Link
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-sidebar-primary text-sidebar-primary-foreground"
                : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
            )}
          >
            {item.icon}
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const items = user ? (NAV[user.role] ?? []) : [];

  const handleLogout = () => {
    logout();
    void navigate({ to: "/login", replace: true });
  };

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col border-r border-sidebar-border bg-sidebar px-4 py-5 lg:flex">
        <Brand />
        <div className="mt-7 flex-1">
          <NavLinks items={items} />
        </div>
        <div className="rounded-lg bg-sidebar-accent/60 p-3">
          <p className="truncate text-sm font-medium text-sidebar-foreground">{user?.name}</p>
          <p className="truncate text-xs text-sidebar-foreground/60">
            {user ? ROLE_LABEL[user.role] : ""}
          </p>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="mt-2 w-full justify-start text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            <LogOut className="size-4" />
            Sign out
          </Button>
        </div>
      </aside>

      <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-border bg-card/90 px-4 py-3 backdrop-blur lg:hidden">
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild>
            <Button variant="outline" size="icon" aria-label="Open navigation">
              <Menu className="size-4" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-72 border-sidebar-border bg-sidebar p-5">
            <SheetTitle className="sr-only">Navigation</SheetTitle>
            <Brand />
            <div className="mt-7">
              <NavLinks items={items} onNavigate={() => setOpen(false)} />
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="mt-6 w-full justify-start text-sidebar-foreground/80 hover:bg-sidebar-accent"
            >
              <LogOut className="size-4" />
              Sign out
            </Button>
          </SheetContent>
        </Sheet>
        <div className="flex items-center gap-2">
          <div className="flex size-8 items-center justify-center rounded-lg bg-accent text-accent-foreground">
            <Truck className="size-4" />
          </div>
          <span className="text-sm font-semibold">SwiftRoute</span>
        </div>
        <span className="text-xs text-muted-foreground">{user?.name}</span>
      </header>

      <main className="lg:pl-64">
        <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:py-8">{children}</div>
      </main>
    </div>
  );
}
