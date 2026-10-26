import Link from "next/link";
import { getRevops } from "@/lib/data";
import { KpiTile } from "@/components/KpiTile";
import { M, R } from "@/lib/types";
import { num, str, pct, dateBR, weekdayBR, bool } from "@/lib/parse";
import { taxaTime, pontos } from "@/lib/team";
import { K } from "@/lib/types";

export default async function Revops({ searchParams }: PageProps<"/revops">) {
  const d = await getRevops();
  const sp = await searchParams;
  const manager = typeof sp.manager === "string" ? sp.manager : "";
  const regiao = typeof sp.regiao === "string" ? sp.regiao : "";
  const regioesValidas = new Set(["Central", "East", "West"]);
  const reps = d.reps.filter((r) => regioesValidas.has(str(r[M.regiao])) && (!manager || str(r[M.manager]) === manager) && (!regiao || str(r[M.regiao]) === regiao));
  const todos = d.reps.filter((r) => regioesValidas.has(str(r[M.regiao])));
  const managers = Array.from(new Set(todos.map((r) => str(r[M.manager])))).sort();
  const regioes = Array.from(new Set(todos.map((r) => str(r[M.regiao])))).sort();
  const sum = (k: string) => reps.reduce((a, r) => a + num(r[k]), 0);
  const kpisVis = d.kpis.filter((r) => reps.some((x) => str(x[M.vendedor]) === str(r[K.vendedor])));
  const tTime = taxaTime(kpisVis);
  const kpiDe = (nome: string) => d.kpis.find((r) => str(r[K.vendedor]) === nome);
  const nomes = new Set(reps.map((x) => str(x[M.vendedor])));
  const recompra = d.recompra.filter((r) => bool(r[R.entra]) && nomes.has(str(r[R.dono])));
  const link = (m: string, g: string) => `/revops?${new URLSearchParams({ ...(m ? { manager: m } : {}), ...(g ? { regiao: g } : {}) }).toString()}`;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-extrabold">RevOps, <span className="display-accent">{weekdayBR(d.config.hoje)}</span></h1>
        <p className="text-sm text-grey">{dateBR(d.config.hoje)} · todos os times · modo {d.config.modoDono}</p>
      </div>

      <div className="flex flex-wrap gap-2 text-sm items-center">
        <span className="font-semibold">Manager:</span>
        <Link href={link("", regiao)} className={`tag ${manager ? "tag-navy" : "tag-gold"}`}>todos</Link>
        {managers.map((m) => <Link key={m} href={link(m, regiao)} className={`tag ${manager === m ? "tag-gold" : "tag-navy"}`}>{m}</Link>)}
        <span className="font-semibold ml-4">Região:</span>
        <Link href={link(manager, "")} className={`tag ${regiao ? "tag-navy" : "tag-gold"}`}>todas</Link>
        {regioes.map((g) => <Link key={g} href={link(manager, g)} className={`tag ${regiao === g ? "tag-gold" : "tag-navy"}`}>{g}</Link>)}
      </div>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KpiTile label="Vendedores no recorte" value={String(reps.length)} hint={manager || regiao ? "filtrado por manager ou região" : "todos os times"} />
        <KpiTile label="Taxa de fechamento" value={pct(tTime)} hint="deals ganhos sobre fechados, 14 meses, no recorte" />
        <KpiTile label="Deals abertos hoje" value={String(sum(M.hojeComoEsta))} hint="deals com conta que estes vendedores estão segurando agora, antes de redistribuir" />
        <KpiTile label="Deals abertos nas carteiras" value={String(sum(M.carteiras))} hint="deals com conta que ficam com eles depois da redistribuição proposta" />
        <KpiTile label="Pra trabalhar agora" value={String(sum(M.p1) + sum(M.p2))} hint="deals limpos e vivos (passos 1 e 2)" />
        <KpiTile label="Pra requalificar" value={String(sum(M.p3))} hint="deals antigos em conta na hora de recomprar (passo 3)" />
        <KpiTile label="Pra confirmar" value={String(sum(M.confirmar))} hint="outro vendedor fechou o mesmo produto na conta depois de o deal abrir: mesmo pedido ou demanda separada?" />
        <KpiTile label="Recompra sem deal" value={String(recompra.length)} hint={`contas na hora de recomprar sem nenhum deal aberto · fila sem conta: ${sum(M.fila)}`} />
      </section>

      <section className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-navy text-offwhite text-left">
            <tr>
              <th className="p-2">Vendedor</th><th className="p-2">Manager</th><th className="p-2">Região</th><th className="p-2">Taxa</th><th className="p-2">vs recorte</th><th className="p-2">Abertos hoje</th><th className="p-2">Nas carteiras</th><th className="p-2">Na lista</th>
              <th className="p-2">P1</th><th className="p-2">P2</th><th className="p-2">P3</th><th className="p-2">P4</th><th className="p-2">Confirmar</th><th className="p-2">Fila</th><th className="p-2">Carteira vs passado</th><th className="p-2">Alerta</th>
            </tr>
          </thead>
          <tbody>
            {reps.map((t) => (
              <tr key={str(t[M.vendedor])} className="border-t border-line">
                <td className="p-2 font-semibold">{str(t[M.vendedor])}</td>
                <td className="p-2">{str(t[M.manager])}</td><td className="p-2">{str(t[M.regiao])}</td>
                <td className="p-2">{(() => { const kp = kpiDe(str(t[M.vendedor])); return kp && num(kp[K.fechados]) > 0 ? pct(kp[K.taxa]) : "sem deals"; })()}</td>
                <td className="p-2">{(() => { const kp = kpiDe(str(t[M.vendedor])); if (!kp || num(kp[K.fechados]) === 0) return ""; const dlt = num(kp[K.taxa]) - tTime; return <span className={`tag ${dlt >= 0 ? "tag-ok" : "tag-bad"}`}>{pontos(dlt)}</span>; })()}</td>
                <td className="p-2">{str(t[M.hojeComoEsta])}</td><td className="p-2">{str(t[M.carteiras])}</td><td className="p-2 font-bold">{str(t[M.naLista])}</td>
                <td className="p-2">{str(t[M.p1])}</td><td className="p-2">{str(t[M.p2])}</td><td className="p-2">{str(t[M.p3])}</td><td className="p-2">{str(t[M.p4])}</td>
                <td className="p-2">{str(t[M.confirmar])}</td>
                <td className="p-2">{str(t[M.fila])}</td>
                <td className="p-2">{t[M.carteiraVsPassado] === "" ? "" : pct(t[M.carteiraVsPassado])} <span className={`tag ${str(t[M.faixa]) === "OK" ? "tag-ok" : str(t[M.faixa]) ? "tag-bad" : "tag-navy"}`}>{str(t[M.faixa]) || "sem carteira"}</span></td>
                <td className="p-2">{str(t[M.alerta]) && <span className="tag tag-bad">{str(t[M.alerta])}</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <p className="text-xs text-grey">Visão de RevOps sobre todos os times. Com login da empresa, só RevOps e diretoria veem esta página.</p>
    </div>
  );
}
