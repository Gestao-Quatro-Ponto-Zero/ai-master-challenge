import { redirect } from "next/navigation";
import Link from "next/link";
import { currentUser } from "@/lib/session";
import { getRep } from "@/lib/data";
import { KpiTile } from "@/components/KpiTile";
import { DealCard } from "@/components/DealCard";
import { QueueCard } from "@/components/QueueCard";
import { RecompraCard } from "@/components/RecompraCard";
import { K, L } from "@/lib/types";
import { num, str, usd, pct, dateBR, weekdayBR } from "@/lib/parse";
import { taxaTime, pontos, posicaoNoTime } from "@/lib/team";

export default async function MeuDia() {
  const user = await currentUser();
  if (!user) redirect("/");
  if (user.papel === "manager") redirect("/manager");
  const d = await getRep(user.email);
  if (!d) redirect("/");
  const k = d.kpi ?? {};
  const lista = d.lista;
  const passo = (n: number) => lista.filter((r) => num(r[L.passo]) === n);
  const foraDoPrazo = d.fila.filter((f) => str(f["Escalada"]) === "Escalar pro manager").length;
  const filaHoje = d.fila.slice(0, d.config.filaPorDia ?? 5);
  const tTime = taxaTime(d.kpisTime);
  const minhaTaxa = num(k[K.taxa]);
  const posicao = posicaoNoTime(d.kpisTime, user.nome);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-extrabold">Meu dia, <span className="display-accent">{weekdayBR(d.config.hoje)}</span></h1>
          <p className="text-sm text-grey">{dateBR(d.config.hoje)} · {user.nome} · time {user.manager} · {user.regiao} · modo {d.config.modoDono}</p>
        </div>
        <Link href="/fila" className="btn-secondary">
          Fila sem conta: {d.fila.length}{foraDoPrazo ? ` (${foraDoPrazo} fora do prazo)` : ""}
        </Link>
      </div>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KpiTile label="Deals na sua lista" value={str(k[K.abertos] ?? lista.length)} hint={`${passo(1).length + passo(2).length + passo(3).length} pra trabalhar até sexta · ${passo(5).length} pra confirmar`} />
        <KpiTile label="Sua taxa de fechamento" value={pct(minhaTaxa)} hint={`time ${pct(tTime)} · você ${pontos(minhaTaxa - tTime)}${posicao ? ` · ${posicao.pos}º de ${posicao.de}` : ""}`} />
        <KpiTile label="Deals ganhos" value={str(k[K.ganhos] ?? "")} hint="nos 14 meses, mais os que você fechou aqui" />
        <KpiTile label="Deals perdidos" value={str(k[K.perdidos] ?? "")} hint={`${str(k[K.fechados] ?? "")} fechados no total`} />
        <KpiTile label="Vendido" value={usd(k[K.vendido])} hint="soma dos seus deals ganhos em 14 meses" />
        <KpiTile label="Contas da sua carteira" value={str(k[K.contas] ?? "")} hint={d.config.modoDono === "Carteiras" ? "contas em que você é o dono" : "contas em que você tem deal aberto"} />
        <KpiTile label="Produtos por conta" value={num(k[K.produtosPorConta]).toFixed(1).replace(".", ",")} hint="quantos produtos diferentes cada conta sua já comprou, em média" />
        <KpiTile label="Compra média por conta" value={usd(k[K.gastoMedio])} hint={`quanto cada conta sua comprou em 14 meses · total ${usd(k[K.gastoTotal])}`} />
      </section>

      {d.modo === "snapshot" && (
        <p className="text-xs text-warn">Modo snapshot: a planilha não está conectada. O que você marcar fica só neste navegador. Com a planilha conectada, cada ação vira uma linha em Atividades.</p>
      )}

      <Bloco titulo="Comece por aqui" sub="Deals limpos e vivos. Recompra mais urgente primeiro, depois valor, depois ICP." rows={[...passo(1), ...passo(2)]} />

      {d.recompra.length > 0 && (
        <section>
          <div className="flex items-baseline gap-3 mb-3">
            <h2 className="text-xl font-extrabold">Recompra sem deal: abrir e ligar</h2>
            <span className="tag tag-gold">{d.recompra.length}</span>
            <span className="text-xs text-grey">Contas suas na hora de recomprar um produto, sem nenhum deal aberto no CRM. O relógio da conta, com ou sem CRM. Marque feito quando abrir o deal ou ligar.</span>
          </div>
          <div className="grid gap-3">{d.recompra.map((r) => <RecompraCard key={`${str(r["Conta"])}|${str(r["Produto"])}`} row={r} />)}</div>
        </section>
      )}
      {filaHoje.length > 0 && (
        <section>
          <div className="flex items-baseline gap-3 mb-3">
            <h2 className="text-xl font-extrabold">Identificar a conta, hoje</h2>
            <span className="tag tag-gold">{filaHoje.length} de {d.fila.length}</span>
            <span className="text-xs text-grey">Depois dos deals vivos. Vivos primeiro, depois pelo preço. {d.config.filaPorDia ?? 5} por dia.</span>
          </div>
          <div className="grid gap-3">{filaHoje.map((f, i) => <QueueCard key={str(f["Oportunidade"])} row={f} contas={d.contas} pos={i + 1} />)}</div>
        </section>
      )}

      <Bloco titulo="Depois" sub={`Deals antigos em conta na hora de recomprar. Requalificar em ${d.config.requalificacaoDias} dias ou fechar como perdido.`} rows={passo(3)} />
      <Bloco titulo="O resto" sub="Produto ainda dentro da janela. Mantenha contato." rows={passo(4)} />
      <Bloco titulo="Confirmar: outro vendedor fechou o produto depois de o deal abrir" sub="Pode ser o mesmo pedido, já atendido por um colega, ou demanda separada. Os dados não dizem qual: confirme com a conta antes de encerrar. Demanda separada confirmada volta pros passos." rows={passo(5)} />
    </div>
  );
}

function Bloco({ titulo, sub, rows }: { titulo: string; sub: string; rows: import("@/lib/types").Row[] }) {
  return (
    <section>
      <div className="flex items-baseline gap-3 mb-3">
        <h2 className="text-xl font-extrabold">{titulo}</h2>
        <span className="tag tag-gold">{rows.length}</span>
        <span className="text-xs text-grey">{sub}</span>
      </div>
      {rows.length === 0 ? (
        <p className="text-sm text-grey">Nada aqui hoje.</p>
      ) : (
        <div className="grid gap-3">{rows.map((r) => <DealCard key={str(r[L.id])} row={r} />)}</div>
      )}
    </section>
  );
}
