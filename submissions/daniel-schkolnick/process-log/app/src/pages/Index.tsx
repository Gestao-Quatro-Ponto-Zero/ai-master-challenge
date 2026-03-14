import React, { useState } from "react";
import { DataProvider, useData } from "@/context/DataContext";
import { KanbanView } from "@/components/KanbanView";
import { DashboardView } from "@/components/DashboardView";
import { FileUpload } from "@/components/FileUpload";
import { LayoutGrid, BarChart3, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type View = "kanban" | "dashboard";

function AppShell() {
  const [view, setView] = useState<View>("kanban");
  const { loading, error } = useData();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-background">
        <Loader2 className="w-6 h-6 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-background">
        <div className="text-center">
          <p className="text-destructive font-bold mb-2">Erro ao carregar dados</p>
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 border-r border-sidebar-border bg-sidebar flex flex-col">
        <div className="p-4 border-b border-sidebar-border">
          <h2 className="text-sm font-bold text-sidebar-primary tracking-tight">SCORE SIZE</h2>
          <p className="text-[10px] text-sidebar-foreground/50 uppercase tracking-widest mt-0.5">Priorização Comercial</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          <SidebarButton icon={<LayoutGrid className="w-4 h-4" />} label="Pipeline" active={view === "kanban"} onClick={() => setView("kanban")} />
          <SidebarButton icon={<BarChart3 className="w-4 h-4" />} label="Dashboard" active={view === "dashboard"} onClick={() => setView("dashboard")} />
        </nav>
        <div className="p-3 border-t border-sidebar-border">
          <FileUpload />
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-hidden">
        {view === "kanban" ? <KanbanView /> : <DashboardView />}
      </main>
    </div>
  );
}

function SidebarButton({ icon, label, active, onClick }: { icon: React.ReactNode; label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm font-semibold transition-colors",
        active
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
      )}
    >
      {icon}
      {label}
    </button>
  );
}

const Index = () => (
  <DataProvider>
    <AppShell />
  </DataProvider>
);

export default Index;
