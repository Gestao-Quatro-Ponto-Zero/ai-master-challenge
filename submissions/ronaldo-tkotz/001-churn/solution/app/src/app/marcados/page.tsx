import { requireUser } from "@/app/lib/auth";
import { listarMarcados, origemMarcado } from "@/engine/marcados";
import { deckAtual, deckDesatualizado } from "@/engine/deckMarcados";
import { TelaShell } from "@/app/components/telas/TelaShell";
import { ListaMarcados } from "@/app/components/telas/ListaMarcados";
import { Apresentacao } from "@/app/components/telas/Apresentacao";

// Reads the app DB at request time — never prerendered.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * The charts marked on the screens (D44) and the presentation built from them as a Minto
 * pyramid (D45). Each chart is a faithful copy of what was on screen.
 */
export default async function MarcadosPage() {
  const user = await requireUser();
  const itens = listarMarcados(user.id).map((m) => ({ ...m, ...origemMarcado(m) }));
  const deck = deckAtual(user.id);
  return (
    <TelaShell
      email={user.email}
      titulo="Gráficos marcados"
      subtitulo="Cópias fiéis dos gráficos marcados nas telas, com o filtro de quando foram marcados. Marque ou desmarque pelo ícone no canto de cada gráfico; depois monte a apresentação."
    >
      <div className="flex flex-col gap-4">
        <Apresentacao deck={deck} desatualizado={deck ? deckDesatualizado(user.id, deck) : false} total={itens.length} />
        <ListaMarcados itens={itens} />
      </div>
    </TelaShell>
  );
}
