import { useMemo, useState } from "react";
import raw from "./data.json";
import { ForcaBars, Heatmap, Matrix, MonthlyBars, MonthlyLines, SatBars, SegmentCI, leitura, type Corr } from "./charts";
import { dec, int, mes, nome, pct, pval, usd } from "./format";
import { useTheme } from "./theme";
import { Hero } from "./hero";

type Mensal = (typeof raw.mensal)[number];
type Seg = { p: number; itens: { nivel: string; n: number; churn: number; taxa: number; ic: [number, number]; mrr_ativo: number }[] };
type Conta = (typeof raw.contas)[number];

const d = raw;
const M: Mensal[] = d.mensal;
const DESDE = "2023-07"; // antes disso a base tem < 120 assinaturas: taxa vira ruído
const Mt = M.filter((m) => m.mes >= DESDE);
const get = (m: string) => M.find((x) => x.mes === m)!;

const SECOES = [
  ["resumo", "Resumo"], ["churn", "Churn subiu?"], ["uso", "Uso cresceu?"], ["satisfacao", "Satisfação ok?"],
  ["definicoes", "Quem saiu?"], ["correlacoes", "Correlações"], ["segmentos", "Segmentos"], ["mapa", "Mapa"],
  ["auditoria", "Auditoria"], ["contas", "Contas"],
] as const;

function Verdict({ tipo, rotulo, children }: { tipo: "true" | "false" | "partial"; rotulo: string; children: React.ReactNode }) {
  return (
    <div className="verdict"><span className={`tag ${tipo}`}>{rotulo}</span><span>{children}</span></div>
  );
}

export default function App() {
  const { pal, isDark, toggle } = useTheme();
  const k = d.kpis;
  const t = d.tendencia_2024 as Record<string, { rho: number; p: number }>;
  const dez = get("2024-12"), set_ = get("2024-09"), jun = get("2024-06"), jan24 = get("2024-01"), jul23 = get("2023-07");
  const sat = d.satisfacao;
  const satResp = sat.filter((s) => s.nota !== "Sem nota").reduce((a, b) => a + b.tickets, 0);
  const satMedia = sat.filter((s) => s.nota !== "Sem nota").reduce((a, b) => a + Number(b.nota) * b.tickets, 0) / satResp;
  const df = d.definicoes;

  return (
    <>
      <header className="top">
        <div className="bar">
          <span className="brand">RavenStack · Churn</span>
          <nav aria-label="Seções">{SECOES.map(([id, l]) => <a key={id} href={`#${id}`}>{l}</a>)}</nav>
          <button className="theme-btn" onClick={toggle} aria-label={isDark ? "Mudar para tema claro" : "Mudar para tema escuro"}>
            {isDark ? "☀ Claro" : "☾ Escuro"}
          </button>
        </div>
      </header>

      <main className="wrap">
        <Hero pal={pal} mensal={M} sat={sat} kpis={k} def={df} />

        {/* ------------------------------------------------------------ CHURN */}
        <section className="block" id="churn">
          <div className="eyebrow">Pergunta 1</div>
          <h2>O churn subiu?</h2>
          <p className="lede">Contar eventos engana quando a base cresce. Comparamos o volume com a taxa (churn ÷ base ativa no início do mês),
            em assinaturas e em receita.</p>
          <div className="grid2">
            <div className="card">
              <h3>Eventos de churn por mês</h3>
              <p className="note">Tabela <code>churn_events</code>, contagem absoluta</p>
              <MonthlyBars data={M} k="eventos_churn" nomeSerie="Eventos" pal={pal} fmt={int} />
              <p className="foot">De {int(jan24.eventos_churn)} em jan/24 para {int(dez.eventos_churn)} em dez/24.</p>
            </div>
            <div className="card">
              <h3>Taxa mensal de churn</h3>
              <p className="note">Assinaturas pagas encerradas e MRR perdido ÷ base ativa no início do mês</p>
              <MonthlyLines data={Mt} pal={pal} fmt={(v) => pct(v)}
                series={[{ k: "taxa_churn_assinaturas", nome: "Assinaturas", cor: "--s1" }, { k: "taxa_churn_mrr", nome: "MRR", cor: "--s2" }]}
                marca={{ mes: "2024-09", texto: "aceleração" }} />
              <p className="foot">Base ativa: {int(jul23.assinaturas_ativas)} assinaturas em jul/23 → {int(dez.assinaturas_ativas)} em dez/24.</p>
            </div>
          </div>
          <Verdict tipo="true" rotulo="Verdade">
            O volume subiu, e a taxa também, a partir de set/24 ({pct(set_.taxa_churn_assinaturas)} → {pct(dez.taxa_churn_assinaturas)} das
            assinaturas; {pct(set_.taxa_churn_mrr)} → {pct(dez.taxa_churn_mrr)} do MRR). Tendência 2024: ρ = {dec(t.taxa_churn_assinaturas.rho, 2)} (p = {pval(t.taxa_churn_assinaturas.p)}).
          </Verdict>
          <div className="warn">⚠ Parte do pico de dez/24 é efeito de borda: 54 dos 167 encerramentos pagos de dezembro caem nos dias 29 a 31, os últimos dias dos dados.
            Sem eles, dezembro fica em 3,6% em apenas 28 dias, ainda acima de todos os meses anteriores (o maior foi {pct(get("2024-11").taxa_churn_assinaturas)} em nov/24).</div>
        </section>

        {/* ------------------------------------------------------------ USO */}
        <section className="block" id="uso">
          <div className="eyebrow">Pergunta 2</div>
          <h2>O uso cresceu?</h2>
          <p className="lede">O produto olha o total. O que importa para retenção é o uso de cada cliente.</p>
          <div className="grid2">
            <div className="card">
              <h3>Eventos de uso por mês (total)</h3>
              <p className="note">Soma de <code>usage_count</code></p>
              <MonthlyBars data={M} k="uso_eventos" nomeSerie="Eventos de uso" pal={pal} fmt={int} />
              <p className="foot">Tendência 2024: ρ = {dec(t.uso_eventos.rho, 2)} (p = {pval(t.uso_eventos.p)}), ou seja, estável.</p>
            </div>
            <div className="card">
              <h3>Eventos de uso por assinatura ativa</h3>
              <p className="note">Uso do mês ÷ assinaturas pagas ativas no mês</p>
              <MonthlyLines data={Mt} pal={pal} fmt={(v) => dec(v, 1)} series={[{ k: "uso_por_assinatura_ativa", nome: "Uso por assinatura", cor: "--s1" }]} />
              <p className="foot">De {dec(jan24.uso_por_assinatura_ativa, 1)} (jan/24) para {dec(dez.uso_por_assinatura_ativa, 1)} (dez/24): queda em todos os meses.</p>
            </div>
          </div>
          <Verdict tipo="false" rotulo="Não por cliente">
            O uso total ficou parado em cerca de 10 mil eventos por mês enquanto a base de assinaturas se multiplicou. Por assinatura,
            o uso caiu {pct(1 - dez.uso_por_assinatura_ativa / jan24.uso_por_assinatura_ativa, 0)} em 2024.
          </Verdict>
          <div className="warn">⚠ Cuidado: 77,7% dos registros de uso caem fora da vigência da própria assinatura (ver Auditoria). A série total é confiável;
            atribuir uso a uma assinatura específica no tempo não é.</div>
        </section>

        {/* ------------------------------------------------------------ SATISFAÇÃO */}
        <section className="block" id="satisfacao">
          <div className="eyebrow">Pergunta 3</div>
          <h2>A satisfação está ok?</h2>
          <p className="lede">Distribuição das notas dos {int(k.tickets)} tickets de suporte (escala de 1 a 5).</p>
          <div className="grid2">
            <div className="card">
              <h3>Tickets por nota de satisfação</h3>
              <p className="note">Em laranja, tickets sem resposta à pesquisa</p>
              <SatBars data={sat} pal={pal} />
            </div>
            <div className="card">
              <h3>Por que o número engana</h3>
              <ul style={{ margin: "6px 0 0", paddingLeft: 18, color: pal["--ink-2"], fontSize: 14 }}>
                <li>A média de <b style={{ color: pal["--ink"] }}>{dec(satMedia, 1)}</b> vem só de {int(satResp)} tickets respondidos.</li>
                <li><b style={{ color: pal["--ink"] }}>{pct(k.pct_sem_nota, 0)}</b> dos tickets não têm nota, e é aí que costuma estar o cliente insatisfeito.</li>
                <li>Não há <b style={{ color: pal["--ink"] }}>nenhuma</b> nota 1 ou 2 em {int(k.tickets)} tickets, o que não acontece numa pesquisa real: ou a escala foi truncada, ou a coleta filtra.</li>
                <li>A nota média da conta não separa quem sai de quem fica (ver Correlações → suporte).</li>
              </ul>
            </div>
          </div>
          <Verdict tipo="partial" rotulo="Mal medida">
            “Satisfação ok” é um artefato de medição: o indicador só enxerga quem respondeu, e a escala não registra insatisfação.
          </Verdict>
        </section>

        {/* ------------------------------------------------------------ DEFINIÇÕES */}
        <section className="block" id="definicoes">
          <div className="eyebrow">Achado que ninguém pediu</div>
          <h2>Quem saiu? Depende de qual tabela você pergunta</h2>
          <p className="lede">A base tem três registros de churn. Eles deveriam descrever as mesmas contas, mas não descrevem.</p>
          <div className="grid2">
            <div className="card">
              <h3>As 500 contas por registro de churn</h3>
              <p className="note"><code>accounts.churn_flag</code> × existência de evento em <code>churn_events</code></p>
              <div className="venn" role="img" aria-label={`Só flag ${df.so_flag}, ambos ${df.ambos}, só evento ${df.so_evento}, nenhum ${df.nenhum}`}>
                <div style={{ flex: df.so_flag, background: pal["--s2"] }}>{df.so_flag}</div>
                <div style={{ flex: df.ambos, background: pal["--s1"] }}>{df.ambos}</div>
                <div style={{ flex: df.so_evento, background: pal["--s3"] }}>{df.so_evento}</div>
                <div style={{ flex: df.nenhum, background: pal["--neutral"], color: pal["--ink"] }}>{df.nenhum}</div>
              </div>
              <div className="venn-legend">
                <span><i style={{ display: "inline-block", width: 10, height: 10, borderRadius: 3, background: pal["--s2"], marginRight: 6 }} />Só flag: {df.so_flag}</span>
                <span><i style={{ display: "inline-block", width: 10, height: 10, borderRadius: 3, background: pal["--s1"], marginRight: 6 }} />Flag e evento: {df.ambos}</span>
                <span><i style={{ display: "inline-block", width: 10, height: 10, borderRadius: 3, background: pal["--s3"], marginRight: 6 }} />Só evento: {df.so_evento}</span>
                <span><i style={{ display: "inline-block", width: 10, height: 10, borderRadius: 3, background: pal["--neutral"], marginRight: 6 }} />Nenhum: {df.nenhum}</span>
              </div>
              <ul style={{ margin: "12px 0 0", paddingLeft: 18, fontSize: 13.5, color: pal["--ink-2"] }}>
                <li>Nenhuma das {int(k.churn_flag)} contas com flag de churn tem todas as assinaturas encerradas: todas seguem pagando.</li>
                <li>{int(df.contas_com_assinatura_encerrada)} contas têm alguma assinatura encerrada.</li>
                <li>Correlação entre as duas definições de conta: ρ = {dec(df.spearman_flag_evento, 2)}, ou seja, nenhuma.</li>
              </ul>
            </div>
            <div className="card">
              <h3>Motivo registrado × comentário do cliente</h3>
              <p className="note">{int(k.eventos_churn)} eventos de churn. Se o motivo fosse confiável, cada motivo concentraria um tipo de comentário.</p>
              <Matrix linhas={d.motivos.linhas} colunas={d.motivos.colunas} valores={d.motivos.valores} pal={pal} isDark={isDark} />
              <p className="foot">Associação (V de Cramér) = 0,06. Exemplo: “preço” aparece tanto com “switched to competitor” quanto com “too expensive”, em proporções quase iguais.</p>
            </div>
          </div>
          <Verdict tipo="false" rotulo="Sem base">
            Sem uma definição única de churn e com motivo de saída preenchido ao acaso, a empresa não consegue nem contar nem explicar o
            churn. Esse é o primeiro problema a resolver.
          </Verdict>
        </section>

        <Correlacoes pal={pal} />
        <Segmentos pal={pal} />

        {/* ------------------------------------------------------------ MAPA */}
        <section className="block" id="mapa">
          <div className="eyebrow">Todas as categorias cruzadas</div>
          <h2>Mapa de correlação entre as tabelas</h2>
          <p className="lede">Spearman entre as variáveis numéricas da base ligada, agrupadas por categoria (perfil, receita, uso, suporte, churn).
            Receita e uso andam juntos porque mais assinaturas geram mais registros de uso. As linhas de churn, no fim, ficam praticamente neutras.</p>
          <div className="card">
            <Heatmap vars={d.spearman.variaveis} vals={d.spearman.valores} pal={pal} isDark={isDark} />
          </div>
        </section>

        {/* ------------------------------------------------------------ AUDITORIA */}
        <section className="block" id="auditoria">
          <div className="eyebrow">Antes de qualquer conclusão</div>
          <h2>Auditoria de ligação entre as tabelas</h2>
          <p className="lede">As chaves ligam 100%, mas as datas entre tabelas não são coerentes. Por isso a base foi ligada por chave e agregada
            no histórico inteiro de cada conta, sem janelas do tipo “90 dias antes do churn”.</p>
          <div className="tbl-wrap">
            <table>
              <thead><tr><th>Checagem</th><th className="num">Resultado</th><th>Leitura</th></tr></thead>
              <tbody>
                {d.auditoria.map((a) => (
                  <tr key={a.checagem}><td>{a.checagem}</td><td className="num">{a.resultado}</td><td style={{ color: pal["--ink-2"] }}>{a.leitura}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <Contas pal={pal} />

        <footer>
          Dados: RavenStack, dataset sintético de River @ Rivalytics (Kaggle, licença MIT). Base gerada pelos scripts
          <code>01</code>–<code>04</code> em <code>solution/scripts</code>. Atualizado em {d.gerado_em.replace("T", " ")}.
        </footer>
      </main>
    </>
  );
}

/* ================================================================== CORRELAÇÕES */
const ALVOS = [
  ["churn_flag_conta", "Conta · flag de churn", ["churn", "retida"]],
  ["churn_tem_evento", "Conta · tem evento de churn", ["com evento", "sem evento"]],
  ["assinatura_encerrada", "Assinatura · encerrada", ["encerrada", "ativa"]],
] as const;
const CATS = [["todas", "Todas"], ["perfil", "Perfil"], ["receita", "Receita"], ["uso", "Uso"], ["suporte", "Suporte"]] as const;

function Correlacoes({ pal }: { pal: ReturnType<typeof useTheme>["pal"] }) {
  const [alvo, setAlvo] = useState<(typeof ALVOS)[number][0]>("churn_flag_conta");
  const [cat, setCat] = useState<(typeof CATS)[number][0]>("todas");
  const fonte = (alvo === "assinatura_encerrada" ? d.correlacoes_assinatura : d.correlacoes.filter((c) => c.alvo === alvo)) as Corr[];
  const rows = fonte.filter((c) => cat === "todas" || c.categoria === cat).sort((a, b) => b.forca - a.forca);
  const rot = ALVOS.find((a) => a[0] === alvo)![2] as unknown as [string, string];
  const sobrev = fonte.filter((c) => c.q < 0.05).length;
  return (
    <section className="block" id="correlacoes">
      <div className="eyebrow">O que causa o churn?</div>
      <h2>Correlação de cada variável com o churn, por categoria</h2>
      <p className="lede">Força de 0 (nenhuma) a 1 (separa perfeitamente quem sai de quem fica). Numéricas: |AUC − 0,5| × 2; categóricas: V de Cramér.
        “q” é o p-valor corrigido para {int(fonte.length)} testes simultâneos (Benjamini-Hochberg): só q &lt; 0,05 conta como efeito real.</p>
      <div className="controls">
        <div className="seg" role="group" aria-label="Definição de churn">
          {ALVOS.map(([id, l]) => <button key={id} aria-pressed={alvo === id} onClick={() => setAlvo(id)}>{l}</button>)}
        </div>
        <div className="seg" role="group" aria-label="Categoria">
          {CATS.map(([id, l]) => <button key={id} aria-pressed={cat === id} onClick={() => setCat(id)}>{l}</button>)}
        </div>
      </div>
      <div className="grid2">
        <div className="card">
          <h3>Força da associação · {rows.length} variáveis</h3>
          <p className="note">Linhas verticais: 0,1 = efeito fraco, 0,2 = moderado. Barras em laranja sobreviveriam à correção. Neste recorte: <b>{sobrev}</b>.</p>
          <ForcaBars rows={rows} pal={pal} />
        </div>
        <div className="card" style={{ padding: 0 }}>
          <div className="tbl-wrap" style={{ border: 0, maxHeight: 620 }}>
            <table>
              <thead><tr><th>Variável</th><th className="num">Força</th><th className="num">p</th><th className="num">q</th><th>Leitura</th></tr></thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.variavel}>
                    <td>{nome(r.variavel)}<div style={{ color: pal["--muted"], fontSize: 11.5 }}>{r.categoria}</div></td>
                    <td className="num">{dec(r.forca, 2)}</td>
                    <td className="num">{pval(r.p)}</td>
                    <td className="num">{pval(r.q)}</td>
                    <td style={{ color: pal["--ink-2"], minWidth: 220 }}>{leitura(r, rot)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <Verdict tipo="false" rotulo="Nenhuma causa isolada">
        Em {int(d.kpis.variaveis_testadas)} testes, nos três recortes de churn, nenhuma variável passa da correção. O maior efeito fica abaixo de 0,15
        (“fraco”). Destaques como DevTools ou canal “event” somem quando se considera o tamanho da amostra.
      </Verdict>
    </section>
  );
}

/* ================================================================== SEGMENTOS */
function Segmentos({ pal }: { pal: ReturnType<typeof useTheme>["pal"] }) {
  const segs = d.segmentos as unknown as Record<string, Seg>;
  const nomes = Object.keys(segs);
  const [dim, setDim] = useState(nomes[0]);
  const s = segs[dim];
  const media = d.kpis.churn_flag / d.kpis.contas;
  return (
    <section className="block" id="segmentos">
      <div className="eyebrow">Quais segmentos estão em risco?</div>
      <h2>Taxa de churn por segmento, com margem de erro</h2>
      <p className="lede">O ponto é a taxa observada (flag de churn da conta); a barra clara é o intervalo de confiança de 95%. Se a barra cruza a linha da
        média, a diferença pode ser acaso.</p>
      <div className="controls">
        <label htmlFor="dim">Segmentar por</label>
        <select id="dim" value={dim} onChange={(e) => setDim(e.target.value)}>
          {nomes.map((n) => <option key={n}>{n}</option>)}
        </select>
        <span className="pill">teste qui-quadrado: p = {pval(s.p)}</span>
      </div>
      <div className="card"><SegmentCI itens={s.itens} media={media} pal={pal} /></div>
    </section>
  );
}

/* ================================================================== CONTAS */
type SortKey = "receita_mrr_ativo" | "uso_eventos" | "suporte_tickets" | "suporte_satisfacao_media" | "churn_eventos" | "perfil_account_name";
function Contas({ pal }: { pal: ReturnType<typeof useTheme>["pal"] }) {
  const [q, setQ] = useState("");
  const [filtro, setFiltro] = useState<"todas" | "churn" | "ativas">("todas");
  const [sort, setSort] = useState<{ k: SortKey; desc: boolean }>({ k: "receita_mrr_ativo", desc: true });
  const [lim, setLim] = useState(25);
  const rows = useMemo(() => {
    const qq = q.trim().toLowerCase();
    return (d.contas as Conta[])
      .filter((c) => filtro === "todas" || (filtro === "churn" ? c.churn_flag_conta : !c.churn_flag_conta))
      .filter((c) => !qq || [c.account_id, c.perfil_account_name, c.perfil_industry, c.perfil_country].join(" ").toLowerCase().includes(qq))
      .sort((a, b) => {
        const va = a[sort.k] ?? -Infinity, vb = b[sort.k] ?? -Infinity;
        const r = va < vb ? -1 : va > vb ? 1 : 0;
        return sort.desc ? -r : r;
      });
  }, [q, filtro, sort]);
  const th = (k: SortKey, l: string, num = true) => (
    <th className={num ? "num" : undefined} aria-sort={sort.k === k ? (sort.desc ? "descending" : "ascending") : "none"}>
      <button onClick={() => setSort((s) => ({ k, desc: s.k === k ? !s.desc : true }))}>{l}{sort.k === k ? (sort.desc ? " ↓" : " ↑") : ""}</button>
    </th>
  );
  return (
    <section className="block" id="contas">
      <div className="eyebrow">Base ligada · account_360</div>
      <h2>Explorar as contas</h2>
      <p className="lede">Uma linha por conta, com as cinco tabelas já cruzadas. Clique no cabeçalho para ordenar.</p>
      <div className="controls">
        <label htmlFor="busca" className="sr-only">Buscar conta</label>
        <input id="busca" type="search" placeholder="Buscar por nome, ID, indústria, país…" value={q} onChange={(e) => { setQ(e.target.value); setLim(25); }} style={{ minWidth: 240 }} />
        <div className="seg" role="group" aria-label="Filtrar por status">
          {(["todas", "churn", "ativas"] as const).map((f) => (
            <button key={f} aria-pressed={filtro === f} onClick={() => { setFiltro(f); setLim(25); }}>
              {f === "todas" ? "Todas" : f === "churn" ? "Com flag de churn" : "Sem flag"}
            </button>
          ))}
        </div>
        <span className="pill">{int(rows.length)} contas</span>
      </div>
      <div className="tbl-wrap">
        <table>
          <thead>
            <tr>
              {th("perfil_account_name", "Conta", false)}<th>Indústria</th><th>País</th><th>Canal</th><th>Plano</th>
              {th("receita_mrr_ativo", "MRR ativo")}{th("uso_eventos", "Uso")}<th className="num">Taxa erro</th>
              {th("suporte_tickets", "Tickets")}{th("suporte_satisfacao_media", "Satisf.")}<th className="num">Sem nota</th>
              <th>Flag churn</th>{th("churn_eventos", "Eventos churn")}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, lim).map((c) => (
              <tr key={c.account_id}>
                <td>{c.perfil_account_name}<div style={{ color: pal["--muted"], fontSize: 11.5 }}>{c.account_id}</div></td>
                <td>{c.perfil_industry}</td><td>{c.perfil_country}</td><td>{c.perfil_referral_source}</td><td>{c.perfil_plan_tier}</td>
                <td className="num">{usd(c.receita_mrr_ativo)}</td>
                <td className="num">{int(c.uso_eventos)}</td>
                <td className="num">{pct(c.uso_taxa_erro)}</td>
                <td className="num">{int(c.suporte_tickets)}</td>
                <td className="num">{c.suporte_satisfacao_media == null ? "—" : dec(c.suporte_satisfacao_media, 1)}</td>
                <td className="num">{pct(c.suporte_pct_sem_nota, 0)}</td>
                <td>{c.churn_flag_conta ? <span className="pill yes">sim</span> : <span className="pill">não</span>}</td>
                <td className="num">{int(c.churn_eventos)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {lim < rows.length && (
        <div style={{ textAlign: "center", marginTop: 12 }}>
          <button className="theme-btn" onClick={() => setLim((l) => l + 50)}>Mostrar mais ({int(rows.length - lim)} restantes)</button>
        </div>
      )}
      <p className="foot" style={{ color: pal["--muted"], fontSize: 12.5 }}>Mês de referência dos dados: {mes("2024-12")}.</p>
    </section>
  );
}
