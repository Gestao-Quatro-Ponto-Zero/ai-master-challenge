/**
 * O negócio por dentro: o score (a qualidade) e o que está em jogo, o porquê do score (a idade,
 * cada resposta e a posição na lista), a chance de fechar e a conta por fator, o grupo, a ação
 * sugerida (que o vendedor aceita ou contesta), as perguntas opcionais e os fatos com o contexto
 * que não decide nada.
 */
import type { ItemFila } from '@lead-scorer/dominio/priorizacao';
import {
  decidir,
  responder,
  type RespostasDoDeal,
  type ValorResposta,
} from '@lead-scorer/dominio/qualificacao';
import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { useApp, type Base } from '../app/contexto';
import { link } from '../app/rotas';
import { Perguntas } from '../qualificacao';
import { formatarData } from '../ui/formato';
import { ContaDoScore } from './ContaDoScore';

type Estado =
  | { tipo: 'carregando' }
  | { tipo: 'nao_encontrado' }
  | { tipo: 'erro'; mensagem: string }
  | { tipo: 'pronto'; item: ItemFila };

/**
 * A frase que a tela anuncia depois de uma resposta: quanto o score mudou e a ação (a resposta
 * muda o score e a ação, nunca o grupo).
 */
export function anunciarMudanca(antes: ItemFila, depois: ItemFila): string {
  const [de, para] = [antes.indicador.score, depois.indicador.score];
  const score =
    de !== para ? 'O score foi de ' + (de ?? '—') + ' para ' + (para ?? '—') + '. ' : '';
  if (depois.proximaAcao.texto !== antes.proximaAcao.texto)
    return score + 'A ação agora é: ' + depois.proximaAcao.texto;
  return (score || 'Resposta registrada. ') + 'A ação continua: ' + depois.proximaAcao.texto;
}

export function TelaDeal({ base, id }: { base: Base; id: string }) {
  const { deps } = useApp();
  const [estado, setEstado] = useState<Estado>({ tipo: 'carregando' });
  const [respostas, setRespostas] = useState<RespostasDoDeal | null>(() =>
    deps.repositorio.ler(id),
  );
  const [anuncio, setAnuncio] = useState('');
  // Só a classificação pedida por último vale: trocar de negócio, responder de novo ou sair da
  // tela invalida as que ainda estão em voo.
  const pedido = useRef(0);

  const classificar = useCallback(
    async (r: RespostasDoDeal | null): Promise<Estado> => {
      try {
        const res = await deps.cliente.item({ dealId: id, respostas: r });
        if (res.ok) return { tipo: 'pronto', item: res.valor };
        if (res.erro.codigo === 'deal_nao_encontrado' || res.erro.codigo === 'entrada_invalida') {
          return { tipo: 'nao_encontrado' };
        }
        return { tipo: 'erro', mensagem: res.erro.mensagem };
      } catch (e: unknown) {
        return { tipo: 'erro', mensagem: e instanceof Error ? e.message : String(e) };
      }
    },
    [deps, id],
  );

  useEffect(() => {
    const meu = ++pedido.current;
    const r = deps.repositorio.ler(id);
    setRespostas(r);
    setAnuncio('');
    setEstado({ tipo: 'carregando' });
    void classificar(r).then((novo) => {
      if (meu === pedido.current) setEstado(novo);
    });
    return () => {
      pedido.current++;
    };
  }, [deps, id, classificar]);

  if (estado.tipo === 'carregando') return <Moldura titulo="Carregando o negócio…" />;
  if (estado.tipo === 'nao_encontrado') {
    return (
      <Moldura titulo="Negócio não encontrado">
        <p>
          Não há negócio com o código {id}. <a href={link.segunda}>Voltar para a lista</a>.
        </p>
      </Moldura>
    );
  }
  if (estado.tipo === 'erro') {
    return (
      <Moldura titulo="Não deu para abrir o negócio">
        <p className="erro">{estado.mensagem}</p>
      </Moldura>
    );
  }

  const { item } = estado;
  const { metodo, politica, textos } = base;

  async function aoResponder(perguntaId: string, valor: ValorResposta) {
    const r = responder(respostas, id, metodo, perguntaId, valor, deps.agoraIso());
    if (!r.ok) {
      setAnuncio(r.erro.mensagem);
      return;
    }
    deps.repositorio.salvar(r.valor);
    void deps.registros.responder({ dealId: id, perguntaId, valor });
    setRespostas(r.valor);
    const meu = ++pedido.current;
    const novo = await classificar(r.valor);
    if (meu !== pedido.current) return;
    if (novo.tipo !== 'pronto') {
      // a resposta já está guardada; a tela continua e avisa que não deu para reclassificar
      setAnuncio(novo.tipo === 'erro' ? novo.mensagem : 'Negócio não encontrado.');
      return;
    }
    setEstado(novo);
    setAnuncio(anunciarMudanca(item, novo.item));
  }

  function aoDecidir(aceita: boolean, motivo: string | null): string | null {
    const r = decidir(
      respostas,
      id,
      metodo,
      { acao: item.proximaAcao.tipo, aceita, motivo },
      deps.agoraIso(),
    );
    if (!r.ok) return r.erro.mensagem;
    deps.repositorio.salvar(r.valor);
    void deps.registros.decidir({ dealId: id, acao: item.proximaAcao.tipo, aceita, motivo });
    setRespostas(r.valor);
    setEstado({ tipo: 'pronto', item: { ...item, decisao: r.valor.decisao } });
    return null;
  }

  const perguntas = metodo.perguntas.filter((p) => p.aplicaEm.includes(item.bloco));
  const { deal, avaliacao, indicador } = item;
  const grupo = textos.grupos[item.bloco];
  return (
    <>
      <section className="topo">
        <div className="container cabeca">
          <p className="eyebrow">
            <a href={link.segunda}>{politica.textos.pagina.titulo}</a> · {deal.id}
          </p>
          <h1 className="titulo">
            {deal.produto} <em>· {deal.conta ?? 'sem dado de conta'}</em>
          </h1>
          <div className="indicador indicador--topo" data-testid="deal-indicador">
            <span className="indicador__numero">{indicador.numero}</span>
            <span className="indicador__rotulo">{indicador.rotulo}</span>
          </div>
          <p className="sub" data-testid="deal-em-jogo">
            {indicador.emJogo}
          </p>
          <p className="sub">
            <span
              className={'etiqueta-bloco etiqueta-bloco--' + item.bloco}
              data-testid="deal-bloco"
            >
              {grupo.titulo}
            </span>{' '}
            <strong data-testid="deal-receita">{indicador.receita}</strong>
          </p>
          <p className="sub" data-testid="deal-preco">
            {indicador.preco}
          </p>
          <p className="leitura">{politica.textos.indicador.aviso}</p>
        </div>
      </section>
      <div className="container principal">
        <p className="sr-only" aria-live="polite" data-testid="deal-anuncio">
          {anuncio}
        </p>
        <section className="painel" data-testid="deal-porque-score">
          <h2>Por que {indicador.numero}</h2>
          <ul className="conta">
            {indicador.porqueScore
              .filter((linha) => linha !== indicador.posicaoTexto)
              .map((linha) => (
                <li key={linha} className="conta__linha">
                  {linha}
                </li>
              ))}
            {indicador.posicaoTexto ? (
              <li className="conta__linha" data-testid="deal-posicao">
                {indicador.posicaoTexto}
              </li>
            ) : null}
          </ul>
        </section>

        <section className="painel">
          <h2>Por que está em {grupo.titulo}</h2>
          <p data-testid="deal-porque">{item.porque}</p>
          <p className="aviso">{grupo.subtitulo}</p>
          {item.bloco === 'nutricao' ? <p className="aviso">{textos.avisos.nutricao}</p> : null}
          {anuncio ? <p className="mudanca">{anuncio}</p> : null}
        </section>

        <AcaoSugerida item={item} aoDecidir={aoDecidir} />

        <section className="painel">
          <h2>{politica.textos.perguntas.titulo}</h2>
          <Perguntas
            perguntas={perguntas}
            respostas={respostas}
            rotulos={{ sim: politica.textos.perguntas.sim, nao: politica.textos.perguntas.nao }}
            aoResponder={(p, v) => void aoResponder(p, v)}
          />
          {metodo.aviso ? <p className="aviso">{metodo.aviso}</p> : null}
        </section>

        <section className="painel">
          <h2>Os fatos</h2>
          <dl className="fatos">
            {avaliacao.fatos.map((f) => (
              <div key={f.id}>
                <dt>{f.rotulo}</dt>
                <dd>{f.detalhe}</dd>
              </div>
            ))}
            {indicador.faixa ? (
              <div>
                <dt>Comparado com</dt>
                <dd>
                  {indicador.n ?? 0} negócios antigos com {indicador.faixa}
                </dd>
              </div>
            ) : null}
            <div>
              <dt>Contexto (não muda a nota)</dt>
              <dd>{avaliacao.contexto.join(' · ')}</dd>
            </div>
            <div>
              <dt>Vendedor</dt>
              <dd>
                {deal.vendedor} · {deal.manager} · {deal.regiao}
              </dd>
            </div>
            <div>
              <dt>Início</dt>
              <dd>
                {deal.dataEngajamento ? formatarData(deal.dataEngajamento) : 'sem data de início'}
              </dd>
            </div>
          </dl>
          <p className="aviso">{textos.avisos.referencia}</p>
        </section>

        <section className="painel" data-testid="deal-chance">
          <h2>{politica.textos.score.conta}</h2>
          <p data-testid="deal-chance-absoluta">{indicador.chanceTexto}</p>
          {indicador.parcelas.length > 0 ? (
            <ContaDoScore parcelas={indicador.parcelas} testid="deal-conta" />
          ) : null}
        </section>
      </div>
    </>
  );
}

function AcaoSugerida({
  item,
  aoDecidir,
}: {
  item: ItemFila;
  aoDecidir: (aceita: boolean, motivo: string | null) => string | null;
}) {
  const [contestando, setContestando] = useState(false);
  const [motivo, setMotivo] = useState('');
  const [erro, setErro] = useState<string | null>(null);
  const { decisao, proximaAcao } = item;

  return (
    <section className="painel">
      <h2>O que fazer</h2>
      <p data-testid="deal-acao">{proximaAcao.texto}</p>
      {decisao && decisao.acao === proximaAcao.tipo ? (
        <p className="mudanca" data-testid="acao-decisao">
          {decisao.aceita ? 'Você aceitou esta ação.' : 'Você contestou: ' + (decisao.motivo ?? '')}
        </p>
      ) : null}
      <div className="acoes">
        <button
          type="button"
          className="botao ls-t-colors"
          data-testid="acao-aceitar"
          onClick={() => {
            setErro(aoDecidir(true, null));
            setContestando(false);
          }}
        >
          Aceitar
        </button>
        <button
          type="button"
          className="botao botao--ghost ls-t-colors"
          data-testid="acao-contestar"
          onClick={() => setContestando(true)}
        >
          Contestar
        </button>
      </div>
      {contestando ? (
        <form
          className="campo"
          onSubmit={(e) => {
            e.preventDefault();
            const msg = aoDecidir(false, motivo);
            setErro(msg);
            if (!msg) setContestando(false);
          }}
        >
          <label htmlFor="acao-motivo">Por que não? (obrigatório)</label>
          <textarea
            id="acao-motivo"
            data-testid="acao-motivo"
            rows={3}
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
          />
          <div className="acoes">
            <button
              type="submit"
              className="botao ls-t-colors"
              data-testid="acao-enviar-contestacao"
            >
              Enviar contestação
            </button>
          </div>
        </form>
      ) : null}
      {erro ? (
        <p className="erro" role="alert">
          {erro}
        </p>
      ) : null}
    </section>
  );
}

function Moldura({ titulo, children }: { titulo: string; children?: ReactNode }) {
  return (
    <div className="container principal">
      <h1 className="bloco__titulo">{titulo}</h1>
      {children}
    </div>
  );
}
