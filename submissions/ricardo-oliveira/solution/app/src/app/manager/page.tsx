import { redirect } from "next/navigation";
import { currentUser } from "@/lib/session";
import { getManager } from "@/lib/data";
import { KpiTile } from "@/components/KpiTile";
import { DealCard } from "@/components/DealCard";
import { M, L } from "@/lib/types";
import { num, str, pct, dateBR, weekdayBR } from "@/lib/parse";
import { taxaTime, pontos } from "@/lib/team";
import { K } from "@/lib/types";

export default async function Manager({ searchParams }: PageProps<"/manager">) {
  const user = await currentUser();
  if (!user) redirect("/");
  if (user.papel !== "manager") redirect("/meu-dia");
  const d = await getManager(user.email);
  if (!d) redirect("/");
  const sp = await searchParams;
  const foco = typeof sp.rep === "string" ? sp.rep : "";
  const r = d.resumo ?? {};
  const alertas = d.time.filter((t) => str(t[M.alerta]) !== "");
  const tTime = taxaTime(d.kpisTime);
  const kpiDe = (nome: string) => d.kpisTime.find((r) => str(r[K.vendedor]) === nome);
  const listaFoco = foco ? d.lista.filter((x) => str(x[L.trabalha]) === foco).sort((a, b) => num(a[L.ordem]) - num(b[L.ordem])) : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-extrabold">Meu time, <span className="display-accent">{weekdayBR(d.config.hoje)}</span></h1>
        <p className="text-sm text-grey">{dateBR(d.config.hoje)} · {user.nome} · {user.regiao} · modo {d.config.modoDono}</p>
      </div>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KpiTile label="Vendedores no time" value={str(r["Vendedores"] ?? d.time.length)} hint={`${alertas.length} com alerta (faixa da carteira, fila vencida ou carga alta)`} />
        <KpiTile label="Taxa de fechamento do time" value={pct(tTime)} hint="deals ganhos sobre fechados, 14 meses" />
        <KpiTile label="Deals abertos hoje" value={str(r["Deals com conta hoje (como está)"] ?? "")} hint="deals com conta que o seu time está segurando agora, antes de redistribuir" />
        <KpiTile label="Deals abertos nas carteiras" value={str(r["Deals com conta (carteiras)"] ?? "")} hint="deals com conta que ficam com o seu time depois da redistribuição proposta" />
        <KpiTile label="Pra trabalhar agora" value={String(num(r["Passo 1"]) + num(r["Passo 2"]))} hint="deals limpos e vivos (passos 1 e 2)" />
        <KpiTile label="Pra requalificar" value={str(r["Passo 3"] ?? "")} hint="deals antigos em conta na hora de recomprar (passo 3)" />
        <KpiTile label="Pra confirmar" value={String(d.time.reduce((a, t) => a + num(t[M.confirmar]), 0))} hint="outro vendedor fechou o mesmo produto na conta depois de o deal abrir: mesmo pedido ou demanda separada?" />
        <KpiTile label="Deals sem conta" value={str(r["Fila sem conta"] ?? "")} hint={`${str(r["Fila fora do prazo"] ?? 0)} passaram do prazo de identificar`} />
      </section>

      <section className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-navy text-offwhite text-left">
            <tr>
              <th className="p-2">Vendedor</th><th className="p-2">Taxa de fechamento</th><th className="p-2">vs time</th><th className="p-2">Abertos hoje</th><th className="p-2">Nas carteiras</th><th className="p-2">Na lista</th>
              <th className="p-2">P1</th><th className="p-2">P2</th><th className="p-2">P3</th><th className="p-2">P4</th><th className="p-2">Até sexta</th><th className="p-2">Confirmar</th>
              <th className="p-2">Fila</th><th className="p-2">Vivos em conta de outro</th><th className="p-2">Carteira vs passado</th><th className="p-2">Alerta</th>
            </tr>
          </thead>
          <tbody>
            {d.time.map((t) => {
              const nome = str(t[M.vendedor]);
              return (
                <tr key={nome} className={`border-t border-line ${foco === nome ? "bg-gold/10" : ""}`}>
                  <td className="p-2 font-semibold"><a href={`/manager?rep=${encodeURIComponent(nome)}`} className="hover:text-gold-dark underline-offset-2 hover:underline">{nome}</a></td>
                  <td className="p-2">{(() => { const kp = kpiDe(nome); return kp && num(kp[K.fechados]) > 0 ? pct(kp[K.taxa]) : "sem deals"; })()}</td>
                  <td className="p-2">{(() => { const kp = kpiDe(nome); if (!kp || num(kp[K.fechados]) === 0) return ""; const dlt = num(kp[K.taxa]) - tTime; return <span className={`tag ${dlt >= 0 ? "tag-ok" : "tag-bad"}`}>{pontos(dlt)}</span>; })()}</td>
                  <td className="p-2">{str(t[M.hojeComoEsta])}</td>
                  <td className="p-2">{str(t[M.carteiras])}</td>
                  <td className="p-2 font-bold">{str(t[M.naLista])}</td>
                  <td className="p-2">{str(t[M.p1])}</td><td className="p-2">{str(t[M.p2])}</td><td className="p-2">{str(t[M.p3])}</td><td className="p-2">{str(t[M.p4])}</td>
                  <td className="p-2">{str(t[M.semana])}</td>
                  <td className="p-2">{str(t[M.confirmar])}</td>
                  <td className="p-2">{str(t[M.fila])}{num(t[M.filaFora]) ? <span className="tag tag-bad ml-1">{str(t[M.filaFora])} fora</span> : null}</td>
                  <td className="p-2">{str(t[M.vivosOutroDono])}</td>
                  <td className="p-2">{t[M.carteiraVsPassado] === "" ? "" : pct(t[M.carteiraVsPassado])} <span className={`tag ${str(t[M.faixa]) === "OK" ? "tag-ok" : str(t[M.faixa]) ? "tag-bad" : "tag-navy"}`}>{str(t[M.faixa]) || "sem carteira"}</span></td>
                  <td className="p-2">{str(t[M.alerta]) && <span className="tag tag-bad">{str(t[M.alerta])}</span>}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      {foco && (
        <section>
          <h2 className="text-xl font-extrabold mb-3">Lista de {foco} <span className="tag tag-gold">{listaFoco.length}</span></h2>
          <div className="grid gap-3">{listaFoco.map((x) => <DealCard key={str(x[L.id])} row={x} readOnly />)}</div>
        </section>
      )}
    </div>
  );
}
