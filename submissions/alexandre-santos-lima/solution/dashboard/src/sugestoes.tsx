import raw from "./sugestoes.json";
import dados from "./data.json";
import mesUso from "./mes_uso.json";
import { dec, int, usd, usdK } from "./format";
import type { Palette } from "./theme";

// Página escrita para quem não é técnico: frases curtas, "X de cada 100", nenhuma sigla.
const S = raw;
const D = dados;
const MOTIVO: Record<string, string> = { budget: "orçamento", competitor: "concorrente", features: "funcionalidades", pricing: "preço", support: "suporte", unknown: "desconhecido" };
const audNum = (txt: string) => {
  const r = D.auditoria.find((a) => a.checagem.startsWith(txt))?.resultado ?? "0";
  return Number(r.replace("%", "").replace(".", "").replace(",", "."));
};
const deCada100 = (fracao: number) => `${dec(fracao * 100, 0)} de cada 100`;

type Acao = { titulo: string; problema: React.ReactNode; fazer: React.ReactNode; pronto: React.ReactNode; quem: string };

function Card({ n, a }: { n: number; a: Acao }) {
  return (
    <article className="acao">
      <div className="acao-head">
        <span className="acao-n">{n}</span>
        <h3>{a.titulo}</h3>
        <span className="pill">{a.quem}</span>
      </div>
      <dl>
        <dt>O problema</dt><dd>{a.problema}</dd>
        <dt>O que fazer</dt><dd>{a.fazer}</dd>
        <dt>Como saber que deu certo</dt><dd>{a.pronto}</dd>
      </dl>
    </article>
  );
}

export const ITENS_SUGESTOES = [
  { id: "plano", titulo: "O plano em 3 passos" },
  { id: "medir", titulo: "Arrumar os registros" },
  { id: "porque", titulo: "Entender por que saem" },
  { id: "investigar", titulo: "Clientes para ligar" },
  { id: "reduzir", titulo: "Reduzir os cancelamentos" },
];

export function Sugestoes({ pal }: { pal: Palette }) {
  const df = D.definicoes;
  const dt = D.datas;
  const im = S.impacto;
  const [dev, evento] = S.hipoteses;
  const faixaAtual = S.curva.find((c) => c.base === S.base_atual)!;
  const semComentario = D.motivos.valores.reduce((a, r) => a + r[D.motivos.colunas.indexOf("(sem comentário)")], 0);
  const desconhecido = D.motivos.valores[D.motivos.linhas.indexOf("unknown")].reduce((a, b) => a + b, 0);

  const medir: Acao[] = [
    {
      titulo: "Contar os cancelamentos de um jeito só", quem: "Dados e Financeiro",
      problema: <>A empresa anota os cancelamentos em dois lugares, e eles não batem: discordam em <b>{int(df.so_flag + df.so_evento)} das {int(D.kpis.contas)} contas</b>.
        E as {int(D.kpis.churn_flag)} contas marcadas como “canceladas” continuam pagando por algum serviço.</>,
      fazer: <>Escolher uma regra única para dizer que um cliente cancelou (por exemplo: “ficou 30 dias sem nenhum serviço pago”) e deixar o
        sistema aplicar essa regra sozinho, sem anotação manual.</>,
      pronto: <>Os dois registros passam a concordar em todas as contas.</>,
    },
    {
      titulo: "Anotar a data certa do cancelamento", quem: "Financeiro",
      problema: <>Dos {int(dt.anuais_encerradas)} contratos <b>anuais</b> cancelados, <b>{int(dt.anuais_menos_1_ano)}</b> aparecem encerrados antes de completar um ano,
        e {int(dt.anuais_menos_30_dias)} em menos de um mês. Contrato anual não termina assim: a data anotada está errada. Com a data errada, não dá para
        saber em que mês os clientes saíram.</>,
      fazer: <>Usar como data do cancelamento a data real do fim do contrato, a mesma do sistema de cobrança. Um contrato anual só termina antes
        do prazo se houver rescisão registrada.</>,
      pronto: <>Nenhum contrato anual encerrado antes do prazo sem rescisão.</>,
    },
    {
      titulo: "Ligar o uso do produto ao cliente certo", quem: "Produto e Engenharia",
      problema: <>Em <b>{dec(audNum("Uso fora"), 0)} de cada 100</b> registros de uso, a data cai fora do período em que o cliente tinha o serviço.
        Mais da metade dos chamados de suporte aparece antes de o cliente existir. E <b>{deCada100(mesUso.stats.pct_usa_depois)}</b> clientes
        “cancelados” continuam usando o produto normalmente.</>,
      fazer: <>Registrar cada uso e cada chamado já com o cliente e o serviço corretos, e fazer o sistema recusar o que não faz sentido
        (por exemplo, uso de um serviço que já foi encerrado).</>,
      pronto: <>Praticamente nenhum uso fora do período contratado e nenhum chamado anterior ao cadastro.</>,
    },
    {
      titulo: "Perguntar o motivo de um jeito que funcione", quem: "Atendimento e Produto",
      problema: <>O motivo anotado não combina com o que o cliente escreveu. Exemplo real: o motivo diz <b>“preço”</b> e o comentário diz
        <b> “troquei pelo concorrente”</b>. Em {int(desconhecido)} cancelamentos o motivo é “desconhecido”, e {int(semComentario)} não têm comentário.</>,
      fazer: <>Na hora de cancelar, o cliente escolhe o motivo numa lista curta e pode explicar com as próprias palavras. Uma inteligência
        artificial lê o texto e avisa quando ele contradiz o motivo escolhido; nesses casos, alguém do atendimento liga para confirmar.</>,
      pronto: <>Quase nenhum motivo “desconhecido”, e motivo e comentário dizendo a mesma coisa.</>,
    },
    {
      titulo: "Ouvir também quem está insatisfeito", quem: "Atendimento",
      problema: <><b>{dec(D.kpis.pct_sem_nota * 10, 0)} de cada 10</b> atendimentos ficam sem nota de satisfação, e nenhum dos {int(D.kpis.tickets)} recebeu
        nota 1 ou 2. A nota média boa (4 de 5) vem só de quem respondeu: o cliente insatisfeito não aparece.</>,
      fazer: <>Conferir se a pesquisa realmente oferece as notas baixas, acompanhar quais clientes nunca respondem e procurar esses clientes.
        Fazer também uma pesquisa de tempos em tempos com cada cliente, e não só depois de um atendimento.</>,
      pronto: <>Aparecem notas de 1 a 5, e a empresa sabe quais clientes não respondem.</>,
    },
    {
      titulo: "Conferir os dados toda semana, automaticamente", quem: "Dados",
      problema: <>Nenhum desses problemas aparece olhando uma planilha de cada vez. Todos só surgiram quando as informações foram cruzadas.</>,
      fazer: <>Rodar toda semana a mesma análise deste painel (ela já está pronta e roda com um único comando) e receber um alerta quando
        algum número piorar.</>,
      pronto: <>Todos os itens da aba Dados → Auditoria dentro do esperado.</>,
    },
  ];

  const hipotese = (h: typeof dev, grupo: string) => (
    <div className="card" key={h.nome}>
      <h3>{grupo}: pode ser só coincidência</h3>
      <p className="note" style={{ margin: "6px 0 0", fontSize: 14 }}>
        <b>{deCada100(h.taxa)}</b> cancelaram, contra {dec(h.taxa_resto * 100, 0)} de cada 100 nos demais clientes. Parece muito, mas são só {int(h.n)} clientes,
        e comparamos cerca de 25 grupos diferentes. Com tantos grupos, é normal que um ou dois pareçam diferentes por acaso.
      </p>
      <p className="note" style={{ margin: "8px 0 0", fontSize: 14 }}>
        Para ter certeza seriam precisos <b>{int(h.contas_necessarias)} clientes</b> desse grupo: no ritmo atual, <b>cerca de {dec(h.anos, 0)} anos</b>.
      </p>
    </div>
  );

  return (
    <>
      <section className="hero2" id="plano">
        <div className="eyebrow">O que fazer</div>
        <h1>Antes de reduzir os cancelamentos, a empresa precisa conseguir medi-los</h1>
        <p className="lede" style={{ maxWidth: 820 }}>Hoje os dados não mostram com segurança quem cancelou, quando cancelou nem por quê. Sem isso,
          não há como saber se uma ação para segurar clientes funcionou. Por isso a ordem importa:</p>
        <ol className="steps">
          <li><span className="step-n">1</span><div><b>Arrumar os registros</b><span>primeiro mês</span><p>Cada cancelamento anotado uma vez só, com a data certa e o motivo real.</p></div></li>
          <li><span className="step-n">2</span><div><b>Entender por que saem</b><span>2º e 3º mês</span><p>Conversar com quem cancelou e olhar de novo os dados, já arrumados.</p></div></li>
          <li><span className="step-n">3</span><div><b>Reduzir os cancelamentos</b><span>a partir do 4º mês</span><p>Testar cada ação em parte dos clientes e comparar com quem não recebeu.</p></div></li>
        </ol>
      </section>

      <section className="block" id="medir">
        <div className="eyebrow">Passo 1 · primeiro mês</div>
        <h2>Arrumar os registros</h2>
        <p className="lede">Seis problemas encontrados nos dados, e como resolver cada um.</p>
        <div className="acoes">{medir.map((a, i) => <Card key={a.titulo} n={i + 1} a={a} />)}</div>
      </section>

      <section className="block" id="porque">
        <div className="eyebrow">Passo 2 · 2º e 3º mês</div>
        <h2>Entender por que os clientes saem</h2>
        <p className="lede">Dois grupos de clientes parecem cancelar mais que os outros, mas com os dados de hoje a diferença pode ser coincidência.
          Esperar a empresa crescer para tirar a dúvida levaria anos. É mais rápido perguntar a quem saiu.</p>
        <div className="grid2">
          {hipotese(dev, "Empresas de ferramentas para programadores (DevTools)")}
          {hipotese(evento, "Clientes que chegaram por eventos")}
        </div>
        <div className="acoes" style={{ marginTop: 16 }}>
          <Card n={1} a={{
            titulo: "Ligar para quem cancelou, começando pelos maiores", quem: "Atendimento",
            problema: <>Em <b>{int(S.n_contas_concordam)} clientes</b> os dois registros concordam que houve cancelamento: são os casos mais confiáveis.
              Juntos, eles cancelaram <b>{usdK(S.mrr_perdido_contas_concordam)} por mês</b> em serviços.</>,
            fazer: <>Ligar para esses clientes com um roteiro curto: o que levou ao cancelamento, quando decidiram e o que os teria feito ficar.
              A lista dos 15 primeiros está logo abaixo.</>,
            pronto: <>Os 15 maiores ouvidos, com o motivo confirmado.</>,
          }} />
          <Card n={2} a={{
            titulo: "Refazer esta análise com os dados arrumados", quem: "Dados",
            problema: <>Hoje nenhuma das informações analisadas (setor, país, plano, uso, atendimento) explica quem cancela. Com os registros
              errados, uma causa real pode estar escondida.</>,
            fazer: <>Depois do passo 1, rodar a análise de novo e responder, nesta ordem: o cliente usa menos o produto antes de cancelar?
              Problemas no atendimento vêm antes do cancelamento? Os dois grupos acima se confirmam?</>,
            pronto: <>Cada pergunta com resposta clara: confirmada ou descartada.</>,
          }} />
        </div>
      </section>

      <section className="block" id="investigar">
        <div className="eyebrow">Lista para o atendimento</div>
        <h2>Os 15 clientes para ligar primeiro</h2>
        <p className="lede">Clientes em que os dois registros concordam que houve cancelamento, do maior para o menor valor cancelado.</p>
        <div className="tbl-wrap">
          <table>
            <thead><tr><th>Cliente</th><th>Setor</th><th>País</th><th>Plano</th><th className="num">Cancelou (por mês)</th><th className="num">Ainda paga (por mês)</th><th>Motivo anotado</th><th>O que o cliente escreveu</th><th className="num">Chamados</th></tr></thead>
            <tbody>
              {S.contas_investigar.map((c) => (
                <tr key={c.id}>
                  <td>{c.nome}<div style={{ color: pal["--muted"], fontSize: 11.5 }}>{c.id}</div></td>
                  <td>{c.industria}</td><td>{c.pais}</td><td>{c.plano}</td>
                  <td className="num">{usd(c.mrr_perdido)}</td><td className="num">{usd(c.mrr_ativo)}</td>
                  <td>{MOTIVO[c.motivo] ?? c.motivo}</td><td style={{ color: pal["--ink-2"] }}>{c.feedback ? `“${c.feedback}”` : "—"}</td>
                  <td className="num">{int(c.tickets)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="foot" style={{ color: pal["--muted"], fontSize: 12.5, marginTop: 8 }}>“Ainda paga” mostra que esses clientes cancelaram só parte dos serviços:
          mais um motivo para conversar. O comentário está como o cliente escreveu, em inglês.</p>
      </section>

      <section className="block" id="reduzir">
        <div className="eyebrow">Passo 3 · a partir do 4º mês</div>
        <h2>Reduzir os cancelamentos</h2>
        <div className="grid2">
          <div className="card">
            <h3>Acompanhar a porcentagem que cancela, não o total</h3>
            <p className="note" style={{ margin: "6px 0 0", fontSize: 14 }}>Hoje, de cada 100 clientes que entram, <b>cerca de {dec(S.safra.taxa * 100, 0)} cancelam</b>.
              É esse número que deve ser acompanhado. O total de cancelamentos por mês sempre sobe quando a empresa cresce: parece piora, mas não é.</p>
          </div>
          <div className="card">
            <h3>Cada cliente a menos cancelando, em cada 100, vale cerca de {int(Math.round(im.assinaturas_por_pp))} assinaturas</h3>
            <p className="note" style={{ margin: "6px 0 0", fontSize: 14 }}>Se, de cada 100 clientes, 1 a menos cancelar, são cerca de {int(Math.round(im.assinaturas_por_pp))} assinaturas mantidas,
              ou <b>entre {usdK(im.assinaturas_por_pp * im.mrr_mediano_cancelada)} e {usdK(im.assinaturas_por_pp * im.mrr_medio_cancelada)} por mês</b> em receita.
              É o tamanho da oportunidade, não uma promessa.</p>
          </div>
        </div>
        <div className="acoes" style={{ marginTop: 16 }}>
          <Card n={1} a={{
            titulo: "Testar cada ação antes de aplicar a todos", quem: "Atendimento e Dados",
            problema: <>O número de cancelamentos muda de um mês para outro naturalmente: hoje fica entre {dec(faixaAtual.lo, 0)} e {dec(faixaAtual.hi, 0)} por mês
              sem nada mudar. Sem comparação, uma melhora pode ser só sorte.</>,
            fazer: <>Aplicar a ação (boas-vindas melhores, contato do atendimento, uma oferta) em parte dos clientes, escolhidos por sorteio, e
              comparar com clientes parecidos que não receberam a ação.</>,
            pronto: <>A ação só é estendida a todos quando quem a recebeu cancela menos do que quem não recebeu.</>,
          }} />
        </div>
      </section>
    </>
  );
}
