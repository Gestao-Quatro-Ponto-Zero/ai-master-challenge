/**
 * Novo negócio: o vendedor descreve um cliente que ainda não está no sistema e vê em que grupo
 * ele entra, a nota, o motivo e o que falta perguntar. Este negócio não é guardado.
 */
import type { NovoLead as DadosNegocio } from '@lead-scorer/dominio/pipeline';
import type { ItemFila } from '@lead-scorer/dominio/priorizacao';
import {
  responder,
  type RespostasDoDeal,
  type ValorResposta,
} from '@lead-scorer/dominio/qualificacao';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useApp, type Base } from '../app/contexto';
import { formatarData, formatarUs } from '../ui/formato';
import { Perguntas } from './Perguntas';

export function NovoLead({ base }: { base: Base }) {
  const { deps } = useApp();
  const { organizacao, resumo, metodo, politica, textos } = base;
  const [vendedor, setVendedor] = useState(organizacao.vendedores[0]?.nome ?? '');
  const [produto, setProduto] = useState(resumo.catalogo[0]?.nome ?? '');
  const [conta, setConta] = useState('');
  const [data, setData] = useState('');
  const [negocio, setNegocio] = useState<DadosNegocio | null>(null);
  const [item, setItem] = useState<ItemFila | null>(null);
  const [respostas, setRespostas] = useState<RespostasDoDeal | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  // Só a classificação pedida por último vale (dois envios seguidos não disputam a tela).
  const pedido = useRef(0);
  useEffect(
    () => () => {
      pedido.current++;
    },
    [],
  );

  async function classificar(n: DadosNegocio, r: RespostasDoDeal | null) {
    const meu = ++pedido.current;
    try {
      const res = await deps.cliente.item({ lead: n, respostas: r });
      if (meu !== pedido.current) return;
      if (!res.ok) {
        setErro(res.erro.mensagem);
        return;
      }
      setErro(null);
      setItem(res.valor);
    } catch (e: unknown) {
      if (meu === pedido.current) setErro(e instanceof Error ? e.message : String(e));
    }
  }

  function enviar(e: FormEvent) {
    e.preventDefault();
    const n: DadosNegocio = {
      vendedor,
      produto,
      ...(conta ? { conta } : {}),
      ...(data ? { dataEngajamento: data } : {}),
    };
    setNegocio(n);
    setRespostas(null);
    setItem(null);
    void classificar(n, null);
  }

  function aoResponder(perguntaId: string, valor: ValorResposta) {
    if (!item || !negocio) return;
    const r = responder(respostas, item.deal.id, metodo, perguntaId, valor, deps.agoraIso());
    if (!r.ok) {
      setErro(r.erro.mensagem);
      return;
    }
    setRespostas(r.valor);
    void classificar(negocio, r.valor);
  }

  const perguntas = item ? metodo.perguntas.filter((p) => p.aplicaEm.includes(item.bloco)) : [];
  return (
    <>
      <section className="topo">
        <div className="container cabeca">
          <p className="eyebrow">Novo negócio</p>
          <h1 className="titulo">
            Apareceu um cliente. <em>Onde ele entra?</em>
          </h1>
          <p className="sub">
            Preencha e veja o grupo, a nota e o que falta perguntar. Este negócio não fica guardado.
          </p>
        </div>
      </section>
      <div className="container principal">
        <form className="painel filtros" data-testid="novo-lead-form" onSubmit={enviar}>
          <div className="campo">
            <label htmlFor="lead-vendedor">Vendedor</label>
            <select
              id="lead-vendedor"
              value={vendedor}
              onChange={(e) => setVendedor(e.target.value)}
            >
              {organizacao.vendedores.map((v) => (
                <option key={v.nome} value={v.nome}>
                  {v.nome}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="lead-produto">Produto</label>
            <select id="lead-produto" value={produto} onChange={(e) => setProduto(e.target.value)}>
              {resumo.catalogo.map((p) => (
                <option key={p.nome} value={p.nome}>
                  {p.nome} ({formatarUs(p.precoTabela)})
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="lead-conta">Empresa (opcional)</label>
            <select id="lead-conta" value={conta} onChange={(e) => setConta(e.target.value)}>
              <option value="">Sem empresa: sem dado, não tira ponto</option>
              {resumo.contas.map((c) => (
                <option key={c.nome} value={c.nome}>
                  {c.nome}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="lead-data">Data de início (opcional)</label>
            <input
              id="lead-data"
              type="date"
              max={resumo.referencia}
              value={data}
              onChange={(e) => setData(e.target.value)}
            />
            <span className="aviso">
              Até {formatarData(resumo.referencia)}. {textos.avisos.referencia}
            </span>
          </div>
          <div className="campo">
            <span className="rotulo" aria-hidden="true">
              &nbsp;
            </span>
            <button type="submit" className="botao ls-t-colors">
              Ver onde ele entra
            </button>
          </div>
        </form>

        <div data-testid="novo-lead-status" aria-live="polite">
          {erro ? <p className="erro">{erro}</p> : null}
          {item ? (
            <section className="painel">
              <h2>
                <span className={'etiqueta-bloco etiqueta-bloco--' + item.bloco}>
                  {textos.grupos[item.bloco].titulo}
                </span>{' '}
                {item.indicador.numero} <span className="aviso">{item.indicador.rotulo}</span>
              </h2>
              <p>{item.indicador.motivo}</p>
              <p>
                <strong>O que fazer:</strong> {item.proximaAcao.texto}
              </p>
              <p className="mudanca">
                {item.pendentes.length > 0
                  ? 'Não qualificado: falta saber ' +
                    item.pendentes.map((p) => p.rotulo.toLowerCase()).join(', ') +
                    '.'
                  : 'Qualificado: as perguntas estão respondidas.'}
              </p>
              <p className="aviso">
                {item.indicador.receita} · {item.indicador.preco} ·{' '}
                {item.avaliacao.contexto.join(' · ')}
              </p>
            </section>
          ) : null}
        </div>

        {item ? (
          <section className="painel">
            <h2>{politica.textos.perguntas.titulo}</h2>
            <Perguntas
              perguntas={perguntas}
              respostas={respostas}
              rotulos={{ sim: politica.textos.perguntas.sim, nao: politica.textos.perguntas.nao }}
              aoResponder={aoResponder}
            />
          </section>
        ) : null}
      </div>
    </>
  );
}
