import { notFound } from "next/navigation";
import { requireUser } from "@/app/lib/auth";
import { TelaShell } from "@/app/components/telas/TelaShell";

export const dynamic = "force-dynamic";

/** Screens 4 and 5 of the design (D22). Each lists its blocks until it is built (ISC-18–19); screens 2 and 3 have their own pages. */
const TELAS: Record<string, { titulo: string; blocos: [string, string][] }> = {
  "4": {
    titulo: "Tela 4 · O que a empresa deveria fazer?",
    blocos: [
      ["B4.1", "Ações priorizadas"],
      ["B4.2", "Correlação ou causa?"],
    ],
  },
  "5": {
    titulo: "Tela 5 · A base e a confiança nos números",
    blocos: [
      ["B5.1", "Alertas que mudam o resultado"],
      ["B5.2", "Definições e reprodutibilidade"],
      ["B5.3", "A base: contas e assinaturas"],
      ["B5.4", "Receita e cobrança"],
    ],
  },
};

export default async function Tela({ params }: { params: Promise<{ n: string }> }) {
  const user = await requireUser();
  const { n } = await params;
  const tela = TELAS[n];
  if (!tela) notFound();

  return (
    <TelaShell email={user.email} titulo={tela.titulo} subtitulo="Em construção.">
      <div className="grid gap-3 md:grid-cols-2">
        {tela.blocos.map(([codigo, nome]) => (
          <div key={codigo} className="rounded-xl border border-dashed border-edge-strong bg-panel/50 p-4">
            <span className="font-mono text-[11px] text-accent">{codigo}</span>
            <div className="mt-1 text-[14px] font-medium text-foreground">{nome}</div>
            <div className="mt-1 text-[11.5px] text-faint">Ainda não construído.</div>
          </div>
        ))}
      </div>
    </TelaShell>
  );
}
