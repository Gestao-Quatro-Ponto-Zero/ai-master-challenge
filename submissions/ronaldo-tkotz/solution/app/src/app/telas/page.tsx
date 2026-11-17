import Link from "next/link";
import { requireUser } from "@/app/lib/auth";
import { listarPaineis, listarTelas } from "@/engine/telasUsuario";
import { TelaShell } from "@/app/components/telas/TelaShell";
import { NovaTela } from "@/app/components/telas/NovaTela";

export const dynamic = "force-dynamic";

/** The user's own screens (D46.2): create one, open one. */
export default async function MinhasTelas() {
  const user = await requireUser();
  const telas = listarTelas(user.id);
  return (
    <TelaShell
      email={user.email}
      titulo="Minhas telas"
      subtitulo="Monte telas suas com o analista: crie uma tela, peça uma análise em português e os gráficos que ele fizer ficam nela."
    >
      <div className="flex max-w-3xl flex-col gap-3">
        <NovaTela />
        {telas.length === 0 ? (
          <p className="text-[12.5px] text-muted">Nenhuma tela ainda.</p>
        ) : (
          <ul className="flex flex-col gap-1.5">
            {telas.map((t) => (
              <li key={t.id}>
                <Link href={`/telas/${t.id}`} className="flex items-center gap-3 rounded-lg border border-edge bg-panel px-3 py-2 text-[13px] text-foreground hover:border-accent">
                  <span className="font-medium">{t.nome}</span>
                  <span className="text-[11.5px] text-faint">{listarPaineis(user.id, t.id).length} painéis</span>
                  <span className="ml-auto text-[11px] text-faint">{t.atualizado_em.slice(0, 10)}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </TelaShell>
  );
}
