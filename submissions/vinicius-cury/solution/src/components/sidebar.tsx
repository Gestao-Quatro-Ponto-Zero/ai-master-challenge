"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Headset,
  Users,
  Play,
  BarChart3,
} from "lucide-react";

const prototypeItems = [
  { href: "/prototype/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/prototype/atendimento", label: "Atendimento (Teste)", icon: Headset },
  { href: "/prototype/operador", label: "Operador", icon: Users },
  { href: "/prototype/simulador", label: "Simulador", icon: Play },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-64 flex-col border-r bg-sidebar text-sidebar-foreground">
      <div className="flex h-14 items-center border-b px-4">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground text-sm font-bold">
            OF
          </div>
          <div>
            <h1 className="text-sm font-semibold leading-none">OptiFlow</h1>
            <p className="text-xs text-muted-foreground">Support Optimizer</p>
          </div>
        </Link>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {/* Prototype section first */}
        <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Protótipo
        </p>
        {prototypeItems.map((item) => {
          const isActive =
            pathname === item.href ||
            pathname.startsWith(item.href);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}

      </nav>

      <div className="border-t p-3">
        <div className="rounded-md bg-muted px-3 py-2">
          <p className="text-xs font-medium text-muted-foreground">
            G4 AI Master Challenge
          </p>
          <p className="text-xs text-muted-foreground/70">
            Challenge 002 — Support
          </p>
        </div>
      </div>
    </aside>
  );
}
