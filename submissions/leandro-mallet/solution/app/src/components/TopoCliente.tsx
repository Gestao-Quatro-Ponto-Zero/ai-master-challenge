"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { pedir } from "@/lib/cliente";

const ABAS = [
  { href: "/painel", rotulo: "Painel" },
  { href: "/pipeline", rotulo: "Pipeline" },
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
            className={`border-b-2 px-3 py-2 text-sm font-semibold ${ativa ? "border-dourado text-branco" : "border-marinho text-dourado-claro hover:text-branco"}`}
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
    <button onClick={trocar} className="rounded-controle border border-dourado px-3 py-1 text-sm text-dourado-claro hover:text-branco">
      Trocar perfil
    </button>
  );
}
