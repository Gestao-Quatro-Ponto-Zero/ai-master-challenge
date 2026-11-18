import type { ReactNode } from "react";
import { tableInventory } from "@/engine/dashboard";
import { dataClock } from "@/engine/calendar";
import { opcoesFiltro } from "@/engine/filtros";
import { Sidebar } from "../dashboard/Sidebar";
import { TopBar } from "../dashboard/TopBar";
import { ConnectDialog } from "../dashboard/ConnectDialog";
import { DataSourceDialog } from "../dashboard/DataSourceDialog";
import { FiltrosBar } from "./FiltrosBar";
import { ChatPanel } from "./ChatPanel";
import { MarcadosProvider } from "./Marcados";
import { RecorteProvider } from "./Recorte";

/**
 * The frame every screen shares (D27): side menu with the three screens (D44), the global
 * filters above, the screen in the middle and the analyst chat as a side panel.
 */
export function TelaShell({
  email,
  titulo,
  subtitulo,
  ajustar = false,
  children,
}: {
  email: string;
  titulo: string;
  subtitulo: string;
  /** Fit the screen to the window: no page scroll, the content fills the height (D32). */
  ajustar?: boolean;
  children: ReactNode;
}) {
  const tables = tableInventory();
  const clock = dataClock();
  const ctx = { source: "RavenStack", tableCount: tables.length, asOf: clock.today, firstDate: clock.firstDate, lastDate: clock.lastDate };

  return (
    <MarcadosProvider>
    <RecorteProvider>
    <div className="flex h-screen overflow-hidden bg-background">
      <div className="hidden lg:block">
        <Sidebar email={email} />
      </div>
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar ctx={ctx} tables={tables} />
        <FiltrosBar opcoes={opcoesFiltro()} />
        {ajustar ? (
          <main className="flex min-h-0 flex-1 flex-col gap-2 overflow-hidden px-4 py-2.5">
            <div className="flex items-baseline gap-3">
              <h1 className="text-[17px] font-semibold leading-tight tracking-tight text-foreground">{titulo}</h1>
              <p className="text-[12px] text-muted">{subtitulo}</p>
            </div>
            <div className="min-h-0 flex-1">{children}</div>
          </main>
        ) : (
          <main className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
            <div className="mb-3">
              <h1 className="text-[18px] font-semibold leading-tight tracking-tight text-foreground">{titulo}</h1>
              <p className="mt-1 max-w-3xl text-[12.5px] leading-relaxed text-muted">{subtitulo}</p>
            </div>
            {children}
          </main>
        )}
      </div>
      <ChatPanel />
      <ConnectDialog />
      <DataSourceDialog />
    </div>
    </RecorteProvider>
    </MarcadosProvider>
  );
}
