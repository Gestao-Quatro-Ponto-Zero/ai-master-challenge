import raw from "./sugestoes.json";
import dados from "./data.json";
import mesUso from "./mes_uso.json";
import { dec, int, pct, pval, usd, usdK } from "./format";
import type { Palette } from "./theme";

const S = raw;
const MOTIVO: Record<string, string> = { budget: "orçamento", competitor: "concorrente", features: "funcionalidades", pricing: "preço", support: "suporte", unknown: "desconhecido" };
const D = dados;
const aud = (txt: string) => D.auditoria.find((a) => a.checagem.startsWith(txt))?.resultado ?? "—";

type Acao = { titulo: string; problema: React.ReactNode; fazer: React.ReactNode; pronto: React.ReactNode; quem: string };

function Card({ n, a }: { n: string; a: Acao }) {
  return (
    <article className="acao">
      <div className="acao-head">
        <span className="acao-n">{n}</span>
        <h3>{a.titulo}</h3>
        <span className="pill">{a.quem}</span>
      </div>
      <dl>
        <dt>O que os dados mostram</dt><dd>{a.problema}</dd>
        <dt>O que fazer</dt><dd>{a.fazer}</dd>
        <dt>Está resolvido quando</dt><dd>{a.pronto}</dd>
      </dl>
    </article>
  );
}

export const ITENS_SUGESTOES = [
  { id: "plano", titulo: "Plano em 3 etapas" },
  { id: "medir", titulo: "Corrigir a medição" },
  { id: "porque", titulo: "Descobrir o porquê" },
  { id: "investigar", titulo: "Contas para ouvir primeiro" },
  { id: "reduzir", titulo: "Reduzir o churn" },
];

export function Sugestoes({ pal }: { pal: Palette }) {
  const df = D.definicoes;
  const dt = D.datas;
  const im = S.impacto;
  const [h1, h2] = S.hipoteses;

  const medir: Acao[] = [
    {
      titulo: "Uma única definição de churn", quem: "Dados + Financeiro",
      problema: <>Os dois registros de churn por conta discordam em <b>{int(df.so_flag + df.so_evento)} de 500 contas</b>, e nenhuma das {int(D.kpis.churn_flag)} contas marcadas como churn tem todas as assinaturas encerradas.</>,
      fazer: <>Definir uma regra só, calculada a partir do faturamento (por exemplo: “conta sem nenhuma assinatura paga ativa há 30 dias”). A flag da conta e a tabela de eventos passam a ser geradas por essa regra, nunca preenchidas à mão.</>,
      pronto: <>As três fontes (flag, eventos, assinaturas) concordam em 100% das contas, verificado automaticamente toda semana.</>,
    },
    {
      titulo: "Data de cancelamento vinda do faturamento", quem: "Financeiro",
      problema: <><b>{int(dt.anuais_menos_1_ano)} de {int(dt.anuais_encerradas)}</b> contratos anuais encerrados duraram menos de um ano, {int(dt.anuais_menos_30_dias)} deles menos de 30 dias. Sem data confiável não há taxa mensal confiável.</>,
      fazer: <>Gravar como data de encerramento a data efetiva do fim do contrato no sistema de cobrança. Um contrato anual só pode terminar antes do prazo com uma rescisão registrada.</>,
      pronto: <>Zero contratos anuais encerrados antes do prazo sem rescisão registrada.</>,
    },
    {
      titulo: "Uso e tickets ligados à conta certa", quem: "Produto + Engenharia",
      problema: <><b>{aud("Uso fora")}</b> do uso cai fora da vigência da assinatura, <b>{aud("Tickets abertos antes")}</b> dos tickets são de antes do cadastro da conta, e {pct(mesUso.stats.pct_usa_depois, 0)} das contas seguem usando o produto depois de “cancelar”.</>,
      fazer: <>Registrar cada evento de uso e cada ticket com a conta e a assinatura validadas no momento em que acontecem. Rejeitar o registro quando a assinatura não está ativa naquela data.</>,
      pronto: <>Menos de 1% do uso fora da vigência e nenhum ticket anterior ao cadastro.</>,
    },
    {
      titulo: "Motivo de saída que explique a saída", quem: "CS + Produto",
      problema: <>O motivo registrado não tem relação com o comentário do cliente (associação de 0,06 numa escala de 0 a 1). {int(D.motivos.valores[D.motivos.linhas.indexOf("unknown")].reduce((a, b) => a + b, 0))} cancelamentos têm motivo “desconhecido” e {int(D.motivos.valores.reduce((a, r) => a + r[D.motivos.colunas.indexOf("(sem comentário)")], 0))} não têm comentário.</>,
      fazer: <>Formulário de cancelamento obrigatório, com lista fechada de motivos e um campo livre. Uma IA lê o texto livre, classifica no mesmo padrão e sinaliza quando o texto contradiz o motivo marcado. O CS confirma os casos sinalizados numa ligação.</>,
      pronto: <>Menos de 5% de motivos “desconhecido”, e o motivo marcado bate com o texto na maioria dos casos (associação acima de 0,5).</>,
    },
    {
      titulo: "Pesquisa de satisfação que capte insatisfação", quem: "CS",
      problema: <><b>{pct(D.kpis.pct_sem_nota, 0)}</b> dos tickets não têm nota e não existe nenhuma nota 1 ou 2 em {int(D.kpis.tickets)} tickets.</>,
      fazer: <>Verificar se o formulário realmente oferece as notas 1 e 2. Medir a taxa de resposta por conta e contatar quem nunca responde. Fazer uma pesquisa periódica por conta, não só ao fechar ticket.</>,
      pronto: <>Notas de 1 a 5 aparecem na base, e a taxa de resposta é acompanhada por conta.</>,
    },
    {
      titulo: "Checagem automática semanal", quem: "Dados",
      problema: <>Todas as falhas acima só apareceram cruzando as tabelas. Nenhuma era visível olhando uma tabela isolada.</>,
      fazer: <>Rodar toda semana o diagnóstico deste painel (um comando só, a skill <code>diagnostico-churn</code>) e alertar quando alguma checagem da auditoria piorar.</>,
      pronto: <>Todas as checagens da aba Dados → Auditoria dentro da meta.</>,
    },
  ];

  return (
    <>
      <section className="hero2" id="plano">
        <div className="eyebrow">Sugestões</div>
        <h1>Primeiro medir direito, depois reduzir o churn</h1>
        <p className="lede" style={{ maxWidth: 820 }}>Hoje os dados não dizem quem saiu, quando nem por quê. Qualquer ação de retenção tomada agora não teria
          como ser avaliada. A ordem abaixo resolve isso primeiro.</p>
        <ol className="steps">
          <li><span className="step-n">1</span><div><b>Corrigir a medição</b><span>primeiros 30 dias</span><p>Uma definição de churn, datas e vínculos confiáveis, motivo e satisfação que funcionem.</p></div></li>
          <li><span className="step-n">2</span><div><b>Descobrir o porquê</b><span>30 a 90 dias</span><p>Ouvir quem saiu e testar as hipóteses com dados já corrigidos.</p></div></li>
          <li><span className="step-n">3</span><div><b>Reduzir o churn</b><span>a partir de 90 dias</span><p>Ações de retenção testadas com grupo de controle, medidas pela métrica certa.</p></div></li>
        </ol>
      </section>

      <section className="block" id="medir">
        <div className="eyebrow">Etapa 1 · primeiros 30 dias</div>
        <h2>Corrigir a medição</h2>
        <p className="lede">Seis correções, cada uma ligada a uma falha encontrada no diagnóstico.</p>
        <div className="acoes">{medir.map((a, i) => <Card key={a.titulo} n={`1.${i + 1}`} a={a} />)}</div>
      </section>

      <section className="block" id="porque">
        <div className="eyebrow">Etapa 2 · 30 a 90 dias</div>
        <h2>Descobrir o porquê</h2>
        <p className="lede">Dois segmentos parecem cancelar mais, mas os dados atuais não bastam para afirmar. Esperar que a base cresça para confirmar levaria anos.
          O caminho mais rápido é perguntar a quem saiu.</p>
        <div className="grid2">
          {[h1, h2].map((h) => (
            <div className="card" key={h.nome}>
              <h3>{h.nome}: hipótese, ainda não conclusão</h3>
              <div className="stats">
                <span><b>{pct(h.taxa, 0)}</b> de churn ({int(h.n)} contas)</span>
                <span><b>{pct(h.taxa_resto, 0)}</b> no restante</span>
                <span><b>p = {pval(h.p_corrigido)}</b> após corrigir para os ~25 segmentos testados</span>
              </div>
              <p className="note" style={{ margin: 0 }}>Para confirmar com dados novos seriam necessárias <b>{int(h.contas_necessarias)} contas</b> do segmento. No ritmo atual,
                de {dec(h.contas_por_ano, 0)} contas novas por ano, isso levaria <b>cerca de {dec(h.anos, 0)} anos</b>.</p>
            </div>
          ))}
        </div>
        <div className="acoes" style={{ marginTop: 16 }}>
          <Card n="2.1" a={{
            titulo: "Entrevistar quem saiu, começando pelo maior valor", quem: "CS",
            problema: <>Em <b>{int(S.n_contas_concordam)} contas</b> os dois registros de churn concordam: são os casos mais confiáveis de saída. Juntas, elas somam <b>{usdK(S.mrr_perdido_contas_concordam)}</b> em MRR de assinaturas encerradas.</>,
            fazer: <>Ligar para essas contas, começando pela lista abaixo, com um roteiro fixo: o que motivou, quando decidiu, o que teria evitado. Registrar as respostas no novo formulário de motivo.</>,
            pronto: <>Pelo menos as 15 contas de maior valor ouvidas, com motivo confirmado.</>,
          }} />
          <Card n="2.2" a={{
            titulo: "Refazer o diagnóstico com os dados corrigidos", quem: "Dados",
            problema: <>Hoje nenhuma das {int(D.kpis.variaveis_testadas)} variáveis testadas explica quem sai. Com vínculos quebrados, um sinal real ficaria escondido.</>,
            fazer: <>Depois da etapa 1, rodar de novo o mesmo diagnóstico e testar, nesta ordem: o uso cai antes do cancelamento? Tickets escalados antecedem a saída? DevTools e o canal “event” se confirmam?</>,
            pronto: <>Cada hipótese confirmada ou descartada com teste estatístico registrado.</>,
          }} />
        </div>
      </section>

      <section className="block" id="investigar">
        <div className="eyebrow">Lista de trabalho para o CS</div>
        <h2>As 15 contas para ouvir primeiro</h2>
        <p className="lede">Contas em que a flag e o evento de churn concordam, ordenadas pelo MRR das assinaturas encerradas.</p>
        <div className="tbl-wrap">
          <table>
            <thead><tr><th>Conta</th><th>Indústria</th><th>País</th><th>Plano</th><th className="num">MRR encerrado</th><th className="num">MRR ainda ativo</th><th className="num">Eventos</th><th>Último motivo registrado</th><th>Comentário do cliente</th><th className="num">Tickets</th><th className="num">Sem nota</th></tr></thead>
            <tbody>
              {S.contas_investigar.map((c) => (
                <tr key={c.id}>
                  <td>{c.nome}<div style={{ color: pal["--muted"], fontSize: 11.5 }}>{c.id}</div></td>
                  <td>{c.industria}</td><td>{c.pais}</td><td>{c.plano}</td>
                  <td className="num">{usd(c.mrr_perdido)}</td><td className="num">{usd(c.mrr_ativo)}</td>
                  <td className="num">{int(c.eventos)}</td><td>{MOTIVO[c.motivo] ?? c.motivo}</td><td style={{ color: pal["--ink-2"] }}>{c.feedback ?? "—"}</td>
                  <td className="num">{int(c.tickets)}</td><td className="num">{c.sem_nota == null ? "—" : pct(c.sem_nota, 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="foot" style={{ color: pal["--muted"], fontSize: 12.5, marginTop: 8 }}>“MRR ainda ativo” mostra que essas contas seguem pagando outras assinaturas: o churn registrado é parcial, mais um motivo para conversar.</p>
      </section>

      <section className="block" id="reduzir">
        <div className="eyebrow">Etapa 3 · a partir de 90 dias</div>
        <h2>Reduzir o churn</h2>
        <div className="grid2">
          <div className="card">
            <h3>Medir pela proporção de cada safra, não pela contagem do mês</h3>
            <div className="stats">
              <span><b>{pct(S.safra.taxa)}</b> das assinaturas de cada safra cancelam hoje</span>
              <span><b>{pct(S.safra.pct_mrr_perdido)}</b> do MRR contratado</span>
            </div>
            <p className="note" style={{ margin: 0 }}>A contagem mensal cresce sozinha quando a base cresce e parece piora. A proporção por safra só se mexe quando a retenção muda de verdade.</p>
          </div>
          <div className="card">
            <h3>Cada ponto percentual a menos vale cerca de {int(Math.round(im.assinaturas_por_pp))} assinaturas</h3>
            <div className="stats">
              <span><b>{int(im.ativas_pagas)}</b> assinaturas pagas ativas</span>
              <span><b>{usdK(im.assinaturas_por_pp * im.mrr_mediano_cancelada)} a {usdK(im.assinaturas_por_pp * im.mrr_medio_cancelada)}</b> de MRR por ponto</span>
            </div>
            <p className="note" style={{ margin: 0 }}>Conta direta: 1% das assinaturas ativas × MRR das assinaturas que já cancelaram (mediana {usd(im.mrr_mediano_cancelada)}, média {usd(im.mrr_medio_cancelada)}). É o tamanho do prêmio, não uma promessa de resultado.</p>
          </div>
        </div>
        <div className="acoes" style={{ marginTop: 16 }}>
          <Card n="3.1" a={{
            titulo: "Toda ação de retenção com grupo de controle", quem: "CS + Dados",
            problema: <>Sem grupo de controle, uma queda no churn depois de uma ação pode ser só variação normal. Por mês, a faixa esperada já vai de {dec(S.curva.find((c) => c.base === S.base_atual)?.lo ?? 0, 0)} a {dec(S.curva.find((c) => c.base === S.base_atual)?.hi ?? 0, 0)} registros com a base atual.</>,
            fazer: <>Separar por sorteio uma parte das contas elegíveis que não recebe a ação (onboarding, contato proativo do CS, oferta). Comparar a proporção que cancela nos dois grupos.</>,
            pronto: <>A ação só é ampliada quando o grupo tratado cancela menos que o grupo de controle, com teste estatístico.</>,
          }} />
        </div>
      </section>
    </>
  );
}
