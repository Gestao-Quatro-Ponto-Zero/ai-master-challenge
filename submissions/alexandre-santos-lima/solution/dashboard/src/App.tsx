import { useMemo, useState } from "react";
import raw from "./data.json";
import mrr from "./mrr.json";
import { Receita } from "./receita";
import { ForcaBars, Heatmap, Matrix, MonthlyBars, MonthlyLines, SafraBars, SatBars, SegmentCI, leitura, type Corr, type Safra } from "./charts";
import { dec, int, mes, nome, pct, pval, usd } from "./format";
import { useTheme } from "./theme";
import { Tecnico, nivelPt } from "./charts";
import { Hero } from "./hero";
import { Relacoes } from "./relacoes";
import { Previsao } from "./previsao";
import { Sugestoes, ITENS_SUGESTOES } from "./sugestoes";
import { Shell, useRota, type Item } from "./layout";

type Mensal = (typeof raw.mensal)[number];
type Seg = { p: number; itens: { nivel: string; n: number; churn: number; taxa: number; ic: [number, number]; mrr_ativo: number }[] };
type Conta = (typeof raw.contas)[number];

const d = raw;
const M: Mensal[] = d.mensal;
const DESDE = "2023-07"; // antes disso a base tem < 120 assinaturas: taxa vira ruído
const Mt = M.filter((m) => m.mes >= DESDE);
const get = (m: string) => M.find((x) => x.mes === m)!;

const ITENS_DIAGNOSTICO: Item[] = [
  { id: "resumo", titulo: "Resumo" }, { id: "churn", titulo: "Cancelamentos" }, { id: "relacoes", titulo: "O que explica os cancelamentos" },
  { id: "uso", titulo: "Uso do produto" }, { id: "satisfacao", titulo: "Satisfação" }, { id: "definicoes", titulo: "Qualidade dos dados" }, { id: "receita", titulo: "Receita registrada" },
  { id: "correlacoes", titulo: "Características do cliente" }, { id: "segmentos", titulo: "Grupos de clientes" }, { id: "previsao", titulo: "Previsão" },
];
const ITENS_DADOS: Item[] = [
  { id: "auditoria", titulo: "Auditoria das tabelas" }, { id: "mapa", titulo: "Mapa de correlação" }, { id: "contas", titulo: "As 500 contas" },
];

function Verdict({ tipo, rotulo, children }: { tipo: "true" | "false" | "partial"; rotulo: string; children: React.ReactNode }) {
  return (
    <div className="verdict"><span className={`tag ${tipo}`}>{rotulo}</span><span>{children}</span></div>
  );
}

export default function App() {
  const { pal, isDark, toggle } = useTheme();
  const pagina = useRota();
  const k = d.kpis;
  const t = d.tendencia_2024 as Record<string, { rho: number; p: number }>;
  const dez = get("2024-12"), jan24 = get("2024-01");
  const sat = d.satisfacao;
  const satResp = sat.filter((s) => s.nota !== "Sem nota").reduce((a, b) => a + b.tickets, 0);
  const satMedia = sat.filter((s) => s.nota !== "Sem nota").reduce((a, b) => a + Number(b.nota) * b.tickets, 0) / satResp;
  const df = d.definicoes;
  const dez23 = get("2023-12");
  const safras = d.safras as unknown as Safra[];
  const dt = d.datas;
  const mediaSafra = safras.reduce((a, b) => a + b.encerradas, 0) / safras.reduce((a, b) => a + b.n, 0);

  return (
    <>
      <Shell pagina={pagina} isDark={isDark} toggle={toggle}
        itens={pagina === "sugestoes" ? ITENS_SUGESTOES : pagina === "dados" ? ITENS_DADOS : ITENS_DIAGNOSTICO}>
        {pagina === "diagnostico" && (<>
        <Hero pal={pal} mensal={M} sat={sat} kpis={k} def={df} safras={safras} mediaSafra={mediaSafra} />

        {/* ------------------------------------------------------------ CHURN */}
        <section className="block" id="churn">
          <div className="eyebrow">Cancelamentos</div>
          <h2>Não há sinal de que os clientes estejam cancelando mais: os cancelamentos crescem junto com o número de clientes</h2>
          <p className="lede">Os cancelamentos por mês ficaram {dec(dez.eventos_churn / dez23.eventos_churn, 0)} vezes maiores de dez/23 a dez/24, mas o número de clientes
            ativos também ficou {dec(dez.assinaturas_ativas / dez23.assinaturas_ativas, 0)} vezes maior. Olhando a porcentagem, não houve piora: de quem entrou em 2023, 12% cancelaram; de quem entrou em 2024, 9%.</p>
          <div className="grid2">
            <div className="card">
              <h3>Cancelamentos por mês</h3>
              <p className="note">Total de cancelamentos registrados em cada mês</p>
              <MonthlyBars data={M} k="eventos_churn" nomeSerie="Eventos" pal={pal} fmt={int} />
              <p className="foot">De {int(dez23.eventos_churn)} em dez/23 para {int(dez.eventos_churn)} em dez/24, enquanto os clientes ativos foram de {int(dez23.assinaturas_ativas)} para {int(dez.assinaturas_ativas)}.</p>
            </div>
            <div className="card">
              <h3>% que cancelou, por trimestre de entrada</h3>
              <p className="note">Clientes agrupados pelo trimestre em que começaram (T1/24 = jan a mar de 2024)</p>
              <SafraBars data={safras} media={mediaSafra} pal={pal} />
              <p className="foot">Em 2024, todos os trimestres ficam entre 8% e 10%. Os de 2023 variam mais (10% a 15%) porque tinham poucos clientes; a barra clara
                tem só {safras[0].n}. As diferenças entre trimestres são do tamanho que o acaso produz.</p>
              <Tecnico><p>% de assinaturas pagas encerradas por trimestre de início. Qui-quadrado sem T1/23: p = {pval(dt.p_safras_sem_2023q1)}.</p></Tecnico>
            </div>
          </div>
          <Verdict tipo="partial" rotulo="Conclusão">
            O número de cancelamentos subiu porque a empresa tem mais clientes. A porcentagem que sai não aumentou: cerca de {dec(mediaSafra * 100, 0)} de cada 100 clientes.
          </Verdict>
          <div className="card" style={{ marginTop: 16 }}>
            <h3>E a porcentagem mensal que dispara no fim de 2024?</h3>
            <p className="note">Cancelados no mês ÷ clientes ativos no início do mês. O salto de outubro a dezembro vem de datas de cancelamento anotadas errado, e não de clientes saindo mais.</p>
            <MonthlyLines data={Mt} pal={pal} fmt={(v) => pct(v)} height={200}
              series={[{ k: "taxa_churn_assinaturas", nome: "Assinaturas", cor: "--s1" }, { k: "taxa_churn_mrr", nome: "MRR", cor: "--s2" }]} />
            <ul style={{ margin: "10px 0 0", paddingLeft: 18, fontSize: 13.5, color: pal["--ink-2"] }}>
              <li><b style={{ color: pal["--ink"] }}>{int(dt.anuais_menos_1_ano)} de {int(dt.anuais_encerradas)}</b> contratos <b style={{ color: pal["--ink"] }}>anuais</b> encerrados duraram menos de um ano, e {int(dt.anuais_menos_30_dias)} menos de 30 dias. Isso não acontece com contrato anual.</li>
              <li>Em qualquer trimestre de entrada, a data do cancelamento cai bem no meio do tempo que sobrava até o fim dos dados. Isso é sinal de data inventada, não de decisão do cliente. Por isso quem entrou no fim de 2024 aparece “cancelando” todo de uma vez em out–dez.</li>
              <li>{54} dos {167} cancelamentos de dez/24 caem nos dias 29 a 31, os últimos dias dos dados.</li>
              <li>Pelo mesmo motivo, não dá para comparar a rapidez com que cada turma de clientes cancela. Por isso a conclusão é “não há sinal de piora”, e não “os cancelamentos caíram”.</li>
            </ul>
          </div>
          <div className="warn">Enquanto a data do cancelamento não for confiável, a porcentagem mensal não serve. O número que vale acompanhar é quantos, de cada 100 clientes que entram, acabam cancelando.</div>
        </section>

        <Relacoes pal={pal} />

        {/* ------------------------------------------------------------ USO */}
        <section className="block" id="uso">
          <div className="eyebrow">Uso do produto</div>
          <h2>O uso total ficou parado, e por cliente caiu</h2>
          <p className="lede">O produto é usado o mesmo tanto que em jan/23. Como o número de clientes cresceu, cada cliente usa bem menos.</p>
          <div className="grid2">
            <div className="card">
              <h3>Uso do produto por mês (total)</h3>
              <p className="note">Quantas vezes as funcionalidades foram usadas no mês</p>
              <MonthlyBars data={M} k="uso_eventos" nomeSerie="Eventos de uso" pal={pal} fmt={int} />
              <p className="foot">Estável o tempo todo: cerca de 10 mil usos por mês.</p>
              <Tecnico><p>Tendência em 2024: ρ = {dec(t.uso_eventos.rho, 2)}, p = {pval(t.uso_eventos.p)} (soma de usage_count).</p></Tecnico>
            </div>
            <div className="card">
              <h3>Uso do produto por cliente</h3>
              <p className="note">Uso do mês dividido pelo número de clientes ativos no mês</p>
              <MonthlyLines data={Mt} pal={pal} fmt={(v) => dec(v, 1)} series={[{ k: "uso_por_assinatura_ativa", nome: "Uso por assinatura", cor: "--s1" }]} />
              <p className="foot">De {dec(jan24.uso_por_assinatura_ativa, 1)} (jan/24) para {dec(dez.uso_por_assinatura_ativa, 1)} (dez/24): queda em todos os meses.</p>
            </div>
          </div>
          <Verdict tipo="partial" rotulo="Conclusão">
            O uso total ficou parado em cerca de 10 mil por mês enquanto o número de clientes se multiplicou. Por cliente, o uso caiu
            {" "}{pct(1 - dez.uso_por_assinatura_ativa / jan24.uso_por_assinatura_ativa, 0)} em 2024.
          </Verdict>
          <div className="warn">⚠ Cuidado: 78 de cada 100 registros de uso têm data fora do período em que o cliente tinha o serviço (ver aba Dados). O total por
            mês é confiável; dizer exatamente qual cliente usou quando, não.</div>
        </section>

        {/* ------------------------------------------------------------ SATISFAÇÃO */}
        <section className="block" id="satisfacao">
          <div className="eyebrow">Satisfação</div>
          <h2>A satisfação parece ok porque só mede quem responde</h2>
          <p className="lede">As notas dadas pelos clientes nos {int(k.tickets)} atendimentos de suporte, numa escala de 1 a 5.</p>
          <div className="grid2">
            <div className="card">
              <h3>Atendimentos por nota de satisfação</h3>
              <p className="note">Em laranja, atendimentos em que o cliente não respondeu à pesquisa</p>
              <SatBars data={sat} pal={pal} />
            </div>
            <div className="card">
              <h3>Por que o número engana</h3>
              <ul style={{ margin: "6px 0 0", paddingLeft: 18, color: pal["--ink-2"], fontSize: 14 }}>
                <li>A média de <b style={{ color: pal["--ink"] }}>{dec(satMedia, 1)}</b> vem só dos {int(satResp)} atendimentos em que o cliente respondeu.</li>
                <li><b style={{ color: pal["--ink"] }}>{pct(k.pct_sem_nota, 0)}</b> dos atendimentos ficaram sem nota, e é aí que costuma estar o cliente insatisfeito.</li>
                <li>Não há <b style={{ color: pal["--ink"] }}>nenhuma</b> nota 1 ou 2 em {int(k.tickets)} atendimentos. Numa pesquisa real isso não acontece: ou as notas baixas não são oferecidas, ou estão sendo descartadas.</li>
                <li>A nota média do cliente não ajuda a prever quem vai cancelar.</li>
              </ul>
            </div>
          </div>
          <Verdict tipo="partial" rotulo="Conclusão">
            A nota média só enxerga quem respondeu, e a base não tem nenhuma nota baixa: o indicador não mede insatisfação.
          </Verdict>
        </section>

        {/* ------------------------------------------------------------ DEFINIÇÕES */}
        <section className="block" id="definicoes">
          <div className="eyebrow">Qualidade dos dados</div>
          <h2>A empresa não sabe ao certo quem saiu, nem por quê</h2>
          <p className="lede">Os cancelamentos são anotados em mais de um lugar. Deveriam apontar os mesmos clientes, mas não apontam.</p>
          <div className="grid2">
            <div className="card">
              <h3>As 500 contas, segundo cada registro</h3>
              <p className="note">A marcação “cancelou” no cadastro da conta × a lista de cancelamentos</p>
              <div className="venn" role="img" aria-label={`Só na marcação ${df.so_flag}, nos dois ${df.ambos}, só na lista ${df.so_evento}, em nenhum ${df.nenhum}`}>
                <div style={{ flex: df.so_flag, background: pal["--s2"] }}>{df.so_flag}</div>
                <div style={{ flex: df.ambos, background: pal["--s1"] }}>{df.ambos}</div>
                <div style={{ flex: df.so_evento, background: pal["--s3"] }}>{df.so_evento}</div>
                <div style={{ flex: df.nenhum, background: pal["--neutral"], color: pal["--ink"] }}>{df.nenhum}</div>
              </div>
              <div className="venn-legend">
                <span><i style={{ display: "inline-block", width: 10, height: 10, borderRadius: 3, background: pal["--s2"], marginRight: 6 }} />Só na marcação da conta: {df.so_flag}</span>
                <span><i style={{ display: "inline-block", width: 10, height: 10, borderRadius: 3, background: pal["--s1"], marginRight: 6 }} />Nos dois: {df.ambos}</span>
                <span><i style={{ display: "inline-block", width: 10, height: 10, borderRadius: 3, background: pal["--s3"], marginRight: 6 }} />Só na lista de cancelamentos: {df.so_evento}</span>
                <span><i style={{ display: "inline-block", width: 10, height: 10, borderRadius: 3, background: pal["--neutral"], marginRight: 6 }} />Em nenhum: {df.nenhum}</span>
              </div>
              <ul style={{ margin: "12px 0 0", paddingLeft: 18, fontSize: 13.5, color: pal["--ink-2"] }}>
                <li>Nenhuma das {int(k.churn_flag)} contas marcadas como “cancelou” encerrou todos os serviços: todas seguem pagando alguma coisa.</li>
                <li>{int(df.contas_com_assinatura_encerrada)} contas encerraram pelo menos um serviço.</li>
                <li>Saber que uma conta está num registro não ajuda a adivinhar se está no outro: os dois não têm relação nenhuma.</li>
              </ul>
            </div>
            <div className="card">
              <h3>Motivo anotado × o que o cliente escreveu</h3>
              <p className="note">{int(k.eventos_churn)} cancelamentos. Se o motivo fosse confiável, cada motivo teria quase sempre o mesmo tipo de comentário. Os números se espalham por igual.</p>
              <Matrix linhas={d.motivos.linhas} colunas={d.motivos.colunas} valores={d.motivos.valores} pal={pal} isDark={isDark} />
              <p className="foot">Exemplo: o motivo “preço” aparece tanto com “troquei pelo concorrente” (switched to competitor) quanto com “muito caro” (too expensive), quase na mesma quantidade.</p>
              <Tecnico><p>Associação entre motivo e comentário: V de Cramér = 0,06 (0 = nenhuma, 1 = total).</p></Tecnico>
            </div>
          </div>
          <Verdict tipo="partial" rotulo="Conclusão">
            Sem um jeito único de anotar cancelamentos e com o motivo preenchido ao acaso, a empresa não consegue nem contar nem explicar quem
            sai. Esse é o primeiro problema a resolver.
          </Verdict>
        </section>

        <Receita pal={pal} />

        <Correlacoes pal={pal} />
        <Segmentos pal={pal} />
        <Previsao pal={pal} />
        </>)}

        {pagina === "dados" && (<>

        {/* ------------------------------------------------------------ AUDITORIA */}
        <section className="block" id="auditoria">
          <div className="eyebrow">Antes de qualquer conclusão</div>
          <h2>As planilhas se ligam pelo cliente certo, mas as datas não fazem sentido</h2>
          <p className="lede">Todas as informações apontam para clientes que existem, mas as datas entre elas se contradizem (uso depois do fim do serviço,
            chamado antes do cadastro). Por isso a análise olha o histórico inteiro de cada cliente, sem depender da data exata.</p>
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

        {/* ------------------------------------------------------------ MAPA */}
        <section className="block" id="mapa">
          <div className="eyebrow">Todas as categorias cruzadas</div>
          <h2>Receita e uso andam juntos; o cancelamento não anda com nada</h2>
          <p className="lede">Cada quadrado cruza duas informações sobre os clientes: azul forte, sobem juntas; vermelho, uma sobe quando a outra desce; claro, sem relação.
            Receita e uso andam juntos porque quem tem mais serviços usa mais. As linhas de cancelamento, no fim, ficam claras: nada anda junto com elas.</p>
          <div className="card">
            <Heatmap vars={d.spearman.variaveis} vals={d.spearman.valores} pal={pal} isDark={isDark} />
          </div>
        </section>

        <Contas pal={pal} />
        </>)}

        {pagina === "sugestoes" && <Sugestoes pal={pal} />}

        <footer>
          Dados: RavenStack, dataset sintético de River @ Rivalytics (Kaggle, licença MIT). Base gerada pelos scripts
          <code>01</code>–<code>07</code> em <code>solution/scripts</code>. Atualizado em {d.gerado_em.replace("T", " ")}.
        </footer>
      </Shell>
    </>
  );
}

/* ================================================================== CORRELAÇÕES */
const ALVOS = [
  ["churn_flag_conta", "Marcação da conta", ["cancelou", "ficou"]],
  ["churn_tem_evento", "Lista de cancelamentos", ["na lista", "fora da lista"]],
  ["assinatura_encerrada", "Serviço encerrado", ["encerrado", "ativo"]],
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
      <div className="eyebrow">Características do cliente</div>
      <h2>Nenhuma característica do cliente, sozinha, explica quem cancela</h2>
      <p className="lede">Testamos cada informação que existe sobre o cliente (setor, país, plano, receita, uso, atendimento) para ver se ela separa quem cancela de
        quem fica. A barra vai de 0 (não separa nada) a 1 (separa perfeitamente). Todas ficam perto de zero.</p>
      <Tecnico><p>Força: |AUC − 0,5| × 2 para números; V de Cramér para categorias. “q” é o p-valor corrigido para {int(fonte.length)} testes simultâneos
        (Benjamini-Hochberg): só q &lt; 0,05 contaria como efeito real.</p></Tecnico>
      <div className="controls">
        <div className="seg" role="group" aria-label="Qual registro de cancelamento usar">
          {ALVOS.map(([id, l]) => <button key={id} aria-pressed={alvo === id} onClick={() => setAlvo(id)}>{l}</button>)}
        </div>
        <div className="seg" role="group" aria-label="Categoria">
          {CATS.map(([id, l]) => <button key={id} aria-pressed={cat === id} onClick={() => setCat(id)}>{l}</button>)}
        </div>
      </div>
      <div className="grid2">
        <div className="card">
          <h3>Força da associação · {rows.length} variáveis</h3>
          <p className="note">Linhas verticais: 0,1 = efeito fraco, 0,2 = moderado. Uma barra laranja indicaria uma causa provável: <b>{sobrev === 0 ? "não há nenhuma" : `${sobrev}`}</b>.</p>
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
      <Verdict tipo="partial" rotulo="Conclusão">
        Em {int(d.kpis.variaveis_testadas)} testes, nenhuma característica separa quem cancela de quem fica além do que o acaso explicaria. Diferenças que
        chamam atenção, como no setor DevTools ou em clientes vindos de eventos, desaparecem quando se considera quantos clientes há em cada grupo.
      </Verdict>
    </section>
  );
}

/* ================================================================== SEGMENTOS */
function Segmentos({ pal }: { pal: ReturnType<typeof useTheme>["pal"] }) {
  const [modo, setModo] = useState<"clientes" | "receita">("clientes");
  const segC = d.segmentos as unknown as Record<string, Seg>;
  const segR = mrr.segmentos_receita as Record<string, { itens: { nivel: string; n: number; taxa: number; ic: number[] }[]; acima: string[]; abaixo: string[] }>;
  const nomes = Object.keys(modo === "clientes" ? segC : segR);
  const [dimSel, setDim] = useState(nomes[0]);
  const dim = nomes.includes(dimSel) ? dimSel : nomes[0];
  const media = modo === "clientes" ? d.kpis.churn_flag / d.kpis.contas : mrr.media_receita;
  const abaixo = modo === "receita" ? segR[dim].abaixo : [];
  return (
    <section className="block" id="segmentos">
      <div className="eyebrow">Grupos de clientes</div>
      <h2>Nenhum grupo de clientes cancela comprovadamente mais que os outros</h2>
      {modo === "clientes" ? (
        <p className="lede">O ponto mostra quantos clientes do grupo cancelaram; a barra clara, a margem de erro. Se a barra cruza a linha da média, a diferença pode
          ser acaso. DevTools (31%) fica raspando acima da média, mas, comparando cerca de 25 grupos, é normal que um pareça diferente por sorte.</p>
      ) : (
        <p className="lede">Aqui cada grupo é medido pela parte da receita mensal que foi cancelada, e não pelo número de clientes. A ordem muda: DevTools volta
          para a média, e França, Reino Unido e clientes vindos de eventos ficam no topo. Mesmo assim, nenhum grupo fica acima da média além da margem de erro.
          Clientes vindos de eventos são os únicos que aparecem no topo nas duas medidas: é a primeira hipótese a investigar.</p>
      )}
      <div className="controls">
        <div className="seg" role="group" aria-label="Como medir">
          <button aria-pressed={modo === "clientes"} onClick={() => setModo("clientes")}>Pela quantidade de clientes</button>
          <button aria-pressed={modo === "receita"} onClick={() => setModo("receita")}>Pela receita</button>
        </div>
        <label htmlFor="dim">Agrupar por</label>
        <select id="dim" value={dim} onChange={(e) => setDim(e.target.value)}>
          {nomes.map((n) => <option key={n}>{n}</option>)}
        </select>
        {modo === "clientes" && (
          <span className="pill">{segC[dim].p < 0.05 ? "diferença improvável de ser acaso" : "diferença pode ser acaso"} (p = {pval(segC[dim].p)})</span>
        )}
      </div>
      <div className="card">
        {modo === "clientes" ? (
          <SegmentCI itens={segC[dim].itens} media={media} pal={pal} />
        ) : (
          <SegmentCI itens={segR[dim].itens} media={media} pal={pal} max={0.36} rotuloN="clientes" rotuloTaxa="% da receita cancelada" rotuloMedia="média da empresa" />
        )}
        {abaixo.length > 0 && (
          <p className="foot">{abaixo.map(nivelPt).join(", ")} fica um pouco abaixo da média, mas, com cerca de 22 grupos comparados, isso também pode ser acaso.</p>
        )}
      </div>
      {modo === "receita" && (
        <Tecnico><p>% do MRR das assinaturas pagas que está em assinaturas encerradas; margem de erro = IC 95% por bootstrap reamostrando contas (4.000 reamostras).
          O MRR é assentos × preço de tabela (ver “Receita registrada”), então serve para comparar grupos, não como valor absoluto.</p></Tecnico>
      )}
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
      <div className="eyebrow">Todos os clientes</div>
      <h2>Os 500 clientes, com todas as informações juntas</h2>
      <p className="lede">Uma linha por cliente, juntando cadastro, serviços, uso, atendimento e cancelamentos. Clique no título de uma coluna para ordenar.</p>
      <div className="controls">
        <label htmlFor="busca" className="sr-only">Buscar conta</label>
        <input id="busca" type="search" placeholder="Buscar por nome, código, setor, país…" value={q} onChange={(e) => { setQ(e.target.value); setLim(25); }} style={{ minWidth: 240 }} />
        <div className="seg" role="group" aria-label="Filtrar por status">
          {(["todas", "churn", "ativas"] as const).map((f) => (
            <button key={f} aria-pressed={filtro === f} onClick={() => { setFiltro(f); setLim(25); }}>
              {f === "todas" ? "Todas" : f === "churn" ? "Marcadas como “cancelou”" : "Não marcadas"}
            </button>
          ))}
        </div>
        <span className="pill">{int(rows.length)} contas</span>
      </div>
      <div className="tbl-wrap">
        <table>
          <thead>
            <tr>
              {th("perfil_account_name", "Cliente", false)}<th>Setor</th><th>País</th><th>Como chegou</th><th>Plano</th>
              {th("receita_mrr_ativo", "Paga por mês")}{th("uso_eventos", "Uso")}<th className="num">Erros no uso</th>
              {th("suporte_tickets", "Chamados")}{th("suporte_satisfacao_media", "Nota")}<th className="num">Sem nota</th>
              <th>Marcada “cancelou”</th>{th("churn_eventos", "Cancelamentos")}
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
