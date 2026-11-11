// "Por que a nota é N" (O-36; FIT absoluto na O-52): a conta numa linha, a barra empilhada com legenda, os motivos com o ícone do grupo
// e os componentes em linhas (cabeçalho com valor e peso; itens com o texto inteiro e os pontos à direita).
import { contaDaNota, contribuicoes, itemFitForaDaConta, itensDoFit, itensDoGrupo, pontosDoItem, ROTULO_GRUPO, valorDoItemFit, type Grupo } from "@/lib/explicacaoNota";
import type { Componente } from "@/lib/tipos";
import { Icone, type NomeIcone } from "./ui/Icones";

const COR: Record<Grupo, string> = { fit: "bg-marinho", heat: "bg-dourado-medio", bonus: "bg-bronze-escuro" };
const ICONE: Record<Grupo, NomeIcone> = { fit: "pessoas", heat: "relogio", bonus: "trofeu" };
const GRUPOS: Grupo[] = ["fit", "heat", "bonus"];
const num = (v: number) => v.toLocaleString("pt-BR", { maximumFractionDigits: 1 });

export function NotaExplicada({
  nota, fit, heat, bonus, componentes, motivos, grupos,
}: { nota: number; fit: number; heat: number; bonus: number; componentes: Componente[]; motivos: string[]; grupos: (Grupo | null)[] }) {
  const partes = contribuicoes(fit, heat, bonus);
  return (
    <div className="mt-3 grid gap-4 text-sm">
      {/* A conta e quanto cada parte soma */}
      <div>
        <p className="font-semibold break-words text-marinho tabular-nums">{contaDaNota(fit, heat, bonus, nota)}</p>
        <div className="mt-2 flex h-2 overflow-hidden rounded-selo bg-trilho" role="img" aria-label={`Nota ${nota}: FIT soma ${num(partes.fit)}, HEAT soma ${num(partes.heat)} e BONUS soma ${num(partes.bonus)}, numa escala até 120.`}>
          {GRUPOS.map((g) => (
            <span key={g} className={COR[g]} style={{ width: `${Math.max(0, (partes[g] / 120) * 100)}%` }} />
          ))}
        </div>
        <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-texto-2" aria-hidden>
          {GRUPOS.map((g) => (
            <li key={g} className="inline-flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-selo ${COR[g]}`} />
              {ROTULO_GRUPO[g].sigla} <span className="font-semibold text-texto tabular-nums">{num(partes[g])}</span>
            </li>
          ))}
        </ul>
        <p className="mt-1.5 text-xs text-texto-2">A nota soma 70% da performance do vendedor neste perfil (FIT), 30% do tempo de atendimento (HEAT) e o bônus da empresa (BONUS, de 0 a 20).</p>
      </div>

      {/* Os motivos, com o ícone do grupo */}
      {motivos.length ? (
        <ul className="grid gap-2">
          {motivos.map((m, i) => {
            const g = grupos[i] ?? null;
            return (
              <li key={i} className="flex gap-2">
                <span className={`mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-controle text-branco ${g ? COR[g] : "bg-cinza-g4"}`} aria-hidden>
                  <Icone nome={g ? ICONE[g] : "info"} className="h-3.5 w-3.5" />
                </span>
                <span className="min-w-0 break-words">
                  {g ? <span className="sr-only">{ROTULO_GRUPO[g].sigla}: </span> : null}
                  {m}
                </span>
              </li>
            );
          })}
        </ul>
      ) : null}

      {/* Componentes em linhas */}
      <div className="divide-y divide-divisoria border-y border-divisoria">
        {GRUPOS.map((g) => {
          const itens = g === "fit" ? itensDoFit(componentes) : itensDoGrupo(componentes, g);
          const valor = g === "fit" ? fit : g === "heat" ? heat : bonus;
          return (
            <section key={g} aria-label={`${ROTULO_GRUPO[g].nome} (${ROTULO_GRUPO[g].sigla})`} className="py-3">
              <div className="flex items-baseline gap-2">
                <span className={`h-2 w-2 shrink-0 self-center rounded-selo ${COR[g]}`} aria-hidden />
                <p className="min-w-0 flex-1 font-semibold break-words">
                  {ROTULO_GRUPO[g].nome} ({ROTULO_GRUPO[g].sigla})
                </p>
                <p className="shrink-0 text-right">
                  <span className="text-base font-semibold tabular-nums">{g === "fit" ? `${num(valor)}%` : valor}</span>
                  <span className="ml-1.5 text-xs text-texto-2">{ROTULO_GRUPO[g].peso}</span>
                </p>
              </div>
              {itens.length ? (
                <ul className="mt-1.5 grid gap-1 pl-4 text-texto-2">
                  {itens.map((c) => (
                    <li key={c.nome} className="flex items-start justify-between gap-3">
                      <span className="min-w-0 break-words">{c.nome}</span>
                      <span className={`shrink-0 text-right whitespace-nowrap tabular-nums ${g === "fit" && itemFitForaDaConta(c) ? "text-texto-2" : "text-texto"}`}>
                        {g === "fit" ? valorDoItemFit(c) : pontosDoItem(c)}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : null}
            </section>
          );
        })}
      </div>
    </div>
  );
}
