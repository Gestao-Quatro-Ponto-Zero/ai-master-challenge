/**
 * Acompanhar a equipe: onde o time está perdendo dinheiro, por filtro (vendedor, manager,
 * região), só para ler. No topo, 4 números, cada um com o rótulo e a frase do que mede; embaixo,
 * a tabela por vendedor com os mesmos números. Não há botão de ação nem aprovação (quem aceita ou
 * contesta é o vendedor, no detalhe do negócio) e não há ranking por taxa de ganho.
 */
import type { Filtro } from '@lead-scorer/dominio/organizacao';
import {
  preencher,
  type EmJogo,
  type Painel,
  type TextoDaMetrica,
} from '@lead-scorer/dominio/priorizacao';
import { useEffect, useState, type ReactNode } from 'react';
import { useApp, type Base } from '../app/contexto';
import { Filtros } from '../organizacao';
import { formatarInteiro } from '../ui/formato';

type Estado =
  { tipo: 'carregando' } | { tipo: 'erro'; mensagem: string } | { tipo: 'pronto'; painel: Painel };

/** "US$ 69.395". */
const dolares = (valor: number) => 'US$ ' + formatarInteiro(valor);

/** "4 · US$ 19.580" (na tabela). */
const nEValor = (e: EmJogo) => formatarInteiro(e.n) + ' · ' + dolares(e.valor);

export function VisaoManager({ base }: { base: Base }) {
  const { deps, respostasCompartilhadas, versaoRegistros } = useApp();
  const [filtro, setFiltro] = useState<Filtro>({});
  const [estado, setEstado] = useState<Estado>({ tipo: 'carregando' });

  useEffect(() => {
    let vivo = true;
    deps.cliente
      .painel({ filtro, respostas: deps.repositorio.listar() })
      .then((r) => {
        if (vivo)
          setEstado(
            r.ok
              ? { tipo: 'pronto', painel: r.valor }
              : { tipo: 'erro', mensagem: r.erro.mensagem },
          );
      })
      .catch((e: unknown) => {
        if (vivo) setEstado({ tipo: 'erro', mensagem: e instanceof Error ? e.message : String(e) });
      });
    return () => {
      vivo = false;
    };
  }, [filtro, deps, versaoRegistros]);

  function mudarFiltro(f: Filtro) {
    setEstado({ tipo: 'carregando' });
    setFiltro(f);
  }

  const t = base.politica.textos.painel;
  return (
    <>
      <section className="topo">
        <div className="container cabeca">
          <p className="eyebrow">{t.titulo}</p>
          <h1 className="titulo">
            Onde o time <em>está perdendo dinheiro?</em>
          </h1>
          <p className="sub">{t.subtitulo}</p>
        </div>
      </section>
      <div className="container principal">
        <Filtros organizacao={base.organizacao} valor={filtro} aoMudar={mudarFiltro} />
        {estado.tipo === 'carregando' ? <p aria-live="polite">Contando…</p> : null}
        {estado.tipo === 'erro' ? <p className="erro">{estado.mensagem}</p> : null}
        {estado.tipo === 'pronto' ? (
          <Metricas painel={estado.painel} base={base} compartilhadas={respostasCompartilhadas} />
        ) : null}
      </div>
    </>
  );
}

function Metrica({
  id,
  texto,
  valores,
  children,
}: {
  id: string;
  texto: TextoDaMetrica;
  valores?: Record<string, string | number>;
  children: ReactNode;
}) {
  return (
    <section className="painel metrica" data-testid={'metrica-' + id}>
      <h2>{texto.titulo}</h2>
      <div className="metrica__valor">{children}</div>
      <p className="metrica__rotulo">{texto.rotulo}</p>
      <p className="aviso">{valores ? preencher(texto.mede, valores) : texto.mede}</p>
    </section>
  );
}

/** Quantos negócios e o que está em jogo neles, numa métrica do topo. */
function NumeroEmJogo({ id, valor }: { id: string; valor: EmJogo }) {
  return (
    <>
      <p className="numero-grande" data-testid={'painel-' + id}>
        {formatarInteiro(valor.n)}
      </p>
      <p data-testid={'painel-' + id + '-valor'}>{dolares(valor.valor)} em jogo</p>
    </>
  );
}

/**
 * As 4 métricas e a tabela por vendedor. A métrica 2 e a coluna de respostas vêm das respostas, e
 * o painel diz de onde: do banco compartilhado ("Respostas gravadas: x de n") ou só deste
 * navegador ("Respostas gravadas neste navegador: x de n").
 */
export function Metricas({
  painel,
  base,
  compartilhadas,
}: {
  painel: Painel;
  base: Base;
  compartilhadas: boolean;
}) {
  const t = base.politica.textos.painel;
  const respostas = preencher(compartilhadas ? t.banco : t.local, {
    x: formatarInteiro(painel.respostas.n),
    n: formatarInteiro(painel.respostas.base),
  });
  const foque = painel.foqueSemConversa;
  return (
    <>
      <div className="metricas">
        <Metrica id="receita" texto={t.receita}>
          <p className="numero-grande" data-testid="painel-receita">
            {dolares(painel.receita)}
          </p>
        </Metrica>

        <Metrica id="foque-sem-conversa" texto={t.foqueSemConversa}>
          <NumeroEmJogo id="foque-sem-conversa" valor={foque} />
          <p>
            De {formatarInteiro(foque.foque)} em Foque agora. Não: {formatarInteiro(foque.nao)} ·
            sem resposta: {formatarInteiro(foque.semResposta)} · sim: {formatarInteiro(foque.sim)}
          </p>
          <p className="aviso" data-testid="painel-respostas">
            {respostas}
          </p>
        </Metrica>

        <Metrica id="parado" texto={t.parado} valores={{ limite: painel.limiteParadoDias }}>
          <NumeroEmJogo id="parado" valor={painel.parado} />
        </Metrica>

        <Metrica id="sem-inicio" texto={t.semInicio}>
          <NumeroEmJogo id="sem-inicio" valor={painel.semInicio} />
        </Metrica>
      </div>

      <section className="secao metricas__tabela" data-testid="painel-vendedores">
        <h2>{t.tabela.titulo}</h2>
        <p className="aviso">{t.tabela.mede}</p>
        <div className="rolagem">
          <table className="tabela">
            <thead>
              <tr>
                <th scope="col">{t.tabela.vendedor}</th>
                <th scope="col">{t.tabela.receita}</th>
                <th scope="col">{t.tabela.foqueSemConversa}</th>
                <th scope="col">{t.tabela.parado}</th>
                <th scope="col">{t.tabela.semInicio}</th>
                <th scope="col">{t.tabela.respostas}</th>
              </tr>
            </thead>
            <tbody>
              {painel.vendedores.map((v) => (
                <tr key={v.vendedor} data-vendedor={v.vendedor}>
                  <th scope="row">{v.vendedor}</th>
                  <td>{dolares(v.receita)}</td>
                  <td>{nEValor(v.foqueSemConversa)}</td>
                  <td>{nEValor(v.parado)}</td>
                  <td>{nEValor(v.semInicio)}</td>
                  <td>
                    {formatarInteiro(v.respostas.n)} de {formatarInteiro(v.respostas.base)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
