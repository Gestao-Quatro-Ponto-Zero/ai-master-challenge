import Link from "next/link";
import type { Usuario } from "@/lib/tipos";
import { AbasTopo, TrocarPerfil } from "./TopoCliente";

const PAPEL: Record<Usuario["papel"], string> = { vendedor: "vendas", manager: "manager", admin: "admin" };

/** Topo em azul-marinho: marca, abas e quem está usando. */
export function Topo({ usuario }: { usuario: Usuario | null }) {
  return (
    <header className="bg-marinho text-branco">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 sm:px-6">
        <Link href={usuario ? "/painel" : "/"} className="font-titulo text-xl font-bold text-branco">
          G4 <span className="text-dourado">Sight</span>
        </Link>
        {usuario ? (
          <>
            <AbasTopo />
            <div className="ml-auto flex items-center gap-3 text-sm">
              <span>
                {usuario.nome}
                <span className="text-dourado-claro">{usuario.papel === "admin" ? "" : `, ${PAPEL[usuario.papel]}`}</span>
              </span>
              <TrocarPerfil />
            </div>
          </>
        ) : null}
      </div>
    </header>
  );
}
