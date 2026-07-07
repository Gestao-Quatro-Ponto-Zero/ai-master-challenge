"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { useSidebar } from "@/lib/hooks/useSidebar";
import { cn } from "@/lib/utils";
import { Sidebar } from "./Sidebar";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, hydrated } = useAuth();
  const { collapsed } = useSidebar();
  const router = useRouter();

  useEffect(() => {
    if (hydrated && !user) router.replace("/");
  }, [hydrated, user, router]);

  if (!hydrated) {
    return (
      <div className="min-h-screen grid place-items-center text-slate-400 text-sm">
        Carregando…
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />
      <main
        className={cn(
          "min-w-0 ml-0 transition-[margin-left] duration-150 ease-out",
          collapsed ? "md:ml-[68px]" : "md:ml-[240px]",
        )}
      >
        {children}
      </main>
    </div>
  );
}
