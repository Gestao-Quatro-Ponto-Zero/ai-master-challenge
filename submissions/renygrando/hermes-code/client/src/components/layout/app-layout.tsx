import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "./app-sidebar";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const style = {
    "--sidebar-width": "16rem",
    "--sidebar-width-icon": "4rem",
  };

  return (
    <SidebarProvider style={style as React.CSSProperties}>
      <div className="flex min-h-screen w-full bg-background selection:bg-secondary/30">
        <AppSidebar />
        <div className="flex flex-col flex-1 min-w-0">
          <header className="h-16 flex items-center justify-between gap-4 px-6 border-b border-border/50 bg-card/50 backdrop-blur-sm sticky top-0 z-30">
            <div className="flex items-center gap-4">
              <SidebarTrigger data-testid="button-sidebar-toggle" />
            </div>
            <div className="flex items-center gap-4">
              <div className="text-xs font-medium text-muted-foreground uppercase tracking-widest bg-secondary/10 px-3 py-1.5 rounded-full border border-secondary/20" data-testid="text-system-status">
                Status: <span className="text-foreground font-bold">Operacional</span>
              </div>
            </div>
          </header>
          <main className="flex-1 overflow-auto p-6 md:p-8 lg:p-10 relative">
            <div className="absolute inset-0 pointer-events-none greek-pattern-bg opacity-40 z-0"></div>
            <div className="relative z-10 max-w-7xl mx-auto">
              {children}
            </div>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
