import type { Metadata } from "next";
import "@fontsource-variable/space-grotesk/wght.css";
import "@fontsource-variable/martian-mono/standard.css";
import "./globals.css";
import { AppShell } from "@/components/app-shell";
import { THEME_BOOTSTRAP } from "@/components/theme-toggle";
import { dateBr } from "@/lib/format";
import { dataset, pipeline } from "@/lib/pipeline";

export const metadata: Metadata = {
  title: { default: "Régua — onde focar hoje", template: "%s · Régua" },
  description: "Priorização de deals para vendedores B2B, com score explicável e fila de deals parados.",
};

const datasetLabel = `${dataset.deals.length.toLocaleString("pt-BR")} deals · ${new Set(dataset.deals.map((d) => d.agent)).size} vendedores`;
const stalledCount = pipeline.filter((s) => s.momentum === "stalled").length;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP }} />
      </head>
      <body>
        <AppShell referenceLabel={dateBr(dataset.referenceDate)} stalledCount={stalledCount} datasetLabel={datasetLabel}>
          {children}
        </AppShell>
      </body>
    </html>
  );
}
