import type { Metadata, Viewport } from "next";
import { Suspense, type ReactNode } from "react";
import { Avisos } from "@/components/Avisos";
import { ProvedorEstagio } from "@/components/Estagio";
import { ModalDeal } from "@/components/ModalDeal";
import { Topo } from "@/components/Topo";
import { dataBR } from "@/lib/calculos";
import { dataNegocio, escritaSoEmMemoria, fonteDosDados, somenteLeitura } from "@/server/repositorio";
import { usuarioAtual } from "@/server/sessao";
import { libreBaskerville, manrope } from "@/tema/fontes";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "G4 Sight", template: "%s · G4 Sight" },
  description: "CRM do time comercial, com a prioridade embutida no pipeline.",
};
export const viewport: Viewport = { width: "device-width", initialScale: 1 };

export default async function Layout({ children }: { children: ReactNode }) {
  const usuario = await usuarioAtual();
  return (
    <html lang="pt-BR" className={`${libreBaskerville.variable} ${manrope.variable}`}>
      <body className="min-h-screen antialiased">
        <Avisos>
          <Topo usuario={usuario} />
          {somenteLeitura() ? (
            <p className="border-b border-tom-atencao-texto/20 bg-tom-atencao px-4 py-2 text-center text-sm text-tom-atencao-texto" role="status">
              Modo somente leitura: o banco não respondeu e as mudanças estão desligadas agora. Os dados mostrados são da última carga.
            </p>
          ) : null}
          <ProvedorEstagio>
            <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6">{children}</main>
            {usuario ? (
              <Suspense fallback={null}>
                <ModalDeal usuario={usuario} somenteLeitura={somenteLeitura()} />
              </Suspense>
            ) : null}
          </ProvedorEstagio>
          <footer className="mx-auto max-w-7xl px-4 pb-8 text-xs text-texto-2 sm:px-6">
            Dados até {dataBR(dataNegocio())}. Fonte: {fonteDosDados() === "banco" ? "banco de dados" : "arquivo"}.
            {escritaSoEmMemoria() ? " Sem banco configurado: as mudanças ficam guardadas só enquanto o servidor está ligado." : ""}
          </footer>
        </Avisos>
      </body>
    </html>
  );
}
