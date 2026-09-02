import type { Metadata } from "next";
import { AppShell } from "@/components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "G4 Focus — Prioridade comercial com evidência",
    template: "%s | G4 Focus",
  },
  description:
    "Transforme o pipeline em uma fila de ação explicável para vendedores e lideranças comerciais.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
