import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "JourneyGraph · Inteligência de retenção governada",
  description: "Demonstração local e segura de inteligência de jornadas de clientes, com evidência descritiva e decisões humanas.",
  applicationName: "JourneyGraph"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body><AppShell>{children}</AppShell></body></html>;
}
