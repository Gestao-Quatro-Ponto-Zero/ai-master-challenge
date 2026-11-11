"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { pedir } from "@/lib/cliente";
import { Botao } from "./ui/Botao";

const ABAS = [
  { href: "/painel", rotulo: "Painel" },
  { href: "/pipeline", rotulo: "Pipeline" },
  { href: "/leads", rotulo: "Leads" },
];

export function AbasTopo() {
  const caminho = usePathname();
  return (
    <nav aria-label="Telas" className="flex gap-1">
      {ABAS.map((a) => {
        const ativa = caminho.startsWith(a.href);
        return (
          <Link
            key={a.href}
            href={a.href}
            aria-current={ativa ? "page" : undefined}
            className={`flex h-10 items-center border-b-2 px-3 text-sm font-semibold ${ativa ? "border-dourado text-branco" : "border-transparent text-dourado-claro hover:text-branco"}`}
          >
            {a.rotulo}
          </Link>
        );
      })}
    </nav>
  );
}

export function TrocarPerfil() {
  const router = useRouter();
  async function trocar() {
    await pedir("/api/perfil", "DELETE");
    router.push("/");
    router.refresh();
  }
  return (
    <Botao nivel="secundario" tamanho="compacto" onClick={trocar}>
      Trocar perfil
    </Botao>
  );
}
