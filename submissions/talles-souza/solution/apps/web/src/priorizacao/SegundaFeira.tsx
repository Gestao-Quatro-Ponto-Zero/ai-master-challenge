/**
 * "Onde focar hoje": a pergunta do vendedor respondida em grupos pela idade do negócio (Foque
 * agora, Siga no ritmo, Aborde primeiro, Nutrição), cada negócio com o indicador e o motivo.
 * Todo texto vem da política; o que vale mais aparece primeiro dentro de cada grupo.
 */
import type { Perfil } from '@lead-scorer/dominio/organizacao';
import { preencher, type Fila, type Grupo, type ItemFila } from '@lead-scorer/dominio/priorizacao';
import { decidir, decidirEmLote } from '@lead-scorer/dominio/qualificacao';
import { useEffect, useMemo, useState } from 'react';
import { useApp, type Base } from '../app/contexto';
import { SeletorPerfil } from '../organizacao';
import { agruparPorGrupo, ORDEM, SLUG, testidDoGrupo } from './blocos';
import { ItemDaFila } from './ItemDaFila';
import { comissaoValida } from '../infra';
import { formatarInteiro } from '../ui/formato';

type EstadoFila =
  | { tipo: 'escolher' }
  | { tipo: 'carregando' }
  | { tipo: 'erro'; mensagem: string }
  | { tipo: 'pronta'; fila: Fila };

/** Quantos negócios cada grupo mostra antes do "mostrar mais". */
const POR_VEZ = 20;

/** O vendedor do perfil guardado, se ainda existe no time; senão null (a tela pergunta "Quem é você?"). */
export function vendedorInicial(base: Base, guardado: Perfil | null): string | null {
  const nomes = base.organizacao.vendedores.map((v) => v.nome);
  if (guardado?.tipo === 'vendedor' && nomes.includes(guardado.nome)) return guardado.nome;
  return null;
}

export function SegundaFeira({ base }: { base: Base }) {
  const { deps, versaoRegistros } = useApp();
  const [vendedor, setVendedor] = useState<string | null>(() =>
    vendedorInicial(base, deps.perfil.ler()),
  );
  const [estado, setEstado] = useState<EstadoFila>(() =>
    vendedor ? { tipo: 'carregando' } : { tipo: 'escolher' },
  );
  const [versao, setVersao] = useState(0);

  useEffect(() => {
    // sem vendedor escolhido não há fila para carregar: a tela pergunta "Quem é você?"
    if (!vendedor) return;
    let vivo = true;
    deps.cliente
      .fila({ filtro: { vendedor }, respostas: deps.repositorio.listar() })
      .then((r) => {
        if (!vivo) return;
        setEstado(
          r.ok ? { tipo: 'pronta', fila: r.valor } : { tipo: 'erro', mensagem: r.erro.mensagem },
        );
      })
      .catch((e: unknown) => {
        if (vivo) setEstado({ tipo: 'erro', mensagem: e instanceof Error ? e.message : String(e) });
      });
    return () => {
      vivo = false;
    };
  }, [vendedor, deps, versao, versaoRegistros]);

  function escolher(nome: string) {
    setEstado({ tipo: 'carregando' });
    setVendedor(nome);
    deps.perfil.salvar({ tipo: 'vendedor', nome });
  }

  function encaminhar(item: ItemFila) {
    const r = decidir(
      deps.repositorio.ler(item.deal.id),
      item.deal.id,
      base.metodo,
      { acao: item.proximaAcao.tipo, aceita: true },
      deps.agoraIso(),
    );
    if (!r.ok) return;
    deps.repositorio.salvar(r.valor);
    void deps.registros.decidir({
      dealId: item.deal.id,
      acao: item.proximaAcao.tipo,
      aceita: true,
    });
    setVersao((v) => v + 1);
  }

  /** "Encaminhar os N" (já confirmado): a mesma decisão, com a mesma data, para cada negócio. */
  function encaminharLote(itens: readonly ItemFila[]) {
    const r = decidirEmLote(
      (id) => deps.repositorio.ler(id),
      itens.map((i) => i.deal.id),
      base.metodo,
      { acao: 'encaminhar_para_nutricao', aceita: true },
      deps.agoraIso(),
    );
    if (!r.ok) return;
    for (const registro of r.valor) deps.repositorio.salvar(registro);
    void deps.registros.decidirLote({
      dealIds: r.valor.map((x) => x.dealId),
      acao: 'encaminhar_para_nutricao',
      aceita: true,
    });
    setVersao((v) => v + 1);
  }

  const { politica } = base;
  const total = estado.tipo === 'pronta' ? estado.fila.contadores.total : null;
  return (
    <>
      <section className="topo">
        <div className="container cabeca">
          <h1 className="titulo">{politica.textos.pagina.titulo}</h1>
          <p className="sub">
            {total === null ? ' ' : preencher(politica.textos.pagina.subtitulo, { n: total })}
          </p>
          <p className="leitura">{politica.textos.indicador.aviso}</p>
          <div className="perfil">
            <SeletorPerfil
              vendedores={base.organizacao.vendedores}
              valor={vendedor}
              aoEscolher={escolher}
              rotulo={politica.textos.pagina.quem}
              escolha={politica.textos.pagina.escolha}
              titulos={{
                foque_agora: base.textos.grupos.foque_agora.titulo,
                siga_no_ritmo: base.textos.grupos.siga_no_ritmo.titulo,
                sem_inicio: base.textos.grupos.sem_inicio.titulo,
                nutricao: base.textos.grupos.nutricao.titulo,
              }}
            />
          </div>
        </div>
      </section>
      <div className="container principal">
        {estado.tipo === 'carregando' ? <p aria-live="polite">Montando a sua lista…</p> : null}
        {estado.tipo === 'erro' ? (
          <p className="erro">Não deu para montar a lista: {estado.mensagem}</p>
        ) : null}
        {estado.tipo === 'escolher' ? (
          <p className="sub" data-testid="quem-e-voce">
            {politica.textos.pagina.quem} {politica.textos.pagina.escolha}.
          </p>
        ) : null}
        {estado.tipo === 'pronta' && estado.fila.contadores.total === 0 ? (
          <p className="sub" data-testid="sem-negocios">
            {politica.textos.pagina.semNegocios}
          </p>
        ) : null}
        {estado.tipo === 'pronta' ? (
          <>
            <ReceitaDaLista fila={estado.fila} base={base} />
            <Grupos
              fila={estado.fila}
              base={base}
              aoEncaminhar={encaminhar}
              aoEncaminharLote={encaminharLote}
            />
          </>
        ) : null}
      </div>
    </>
  );
}

/** Arredondado, fica abaixo de US$ 1: a tela diz "quase nada" em vez de "cerca de US$ 0". */
function quaseNada(valor: number): boolean {
  return Math.round(valor) < 1;
}

/**
 * A receita esperada da lista, no topo: quanto deve sair dos negócios abertos hoje nos próximos
 * 3 meses (chance pela idade × preço de tabela), o aviso do que a conta não é e quantos negócios
 * ficam fora dela por não ter data de início.
 */
export function ReceitaDaLista({ fila, base }: { fila: Fila; base: Base }) {
  const { deps } = useApp();
  const textos = base.politica.textos.receita;
  const { total, semEstimativa } = fila.receita;
  const [comissao, setComissao] = useState(() => {
    const guardada = deps.comissao.ler();
    return guardada === null ? '' : String(guardada);
  });
  const percentual = comissao.trim() === '' ? null : Number(comissao.replace(',', '.'));
  const valida = percentual !== null && comissaoValida(percentual);
  const valorComissao = valida ? (total * percentual) / 100 : 0;

  function mudarComissao(texto: string) {
    setComissao(texto);
    const n = texto.trim() === '' ? null : Number(texto.replace(',', '.'));
    deps.comissao.salvar(n !== null && comissaoValida(n) ? n : null);
  }

  return (
    <section className="painel receita" data-testid="receita">
      <p className="receita__total" data-testid="receita-total">
        {quaseNada(total)
          ? textos.totalQuaseNada
          : preencher(textos.total, { total: formatarInteiro(total) })}
      </p>
      <p className="aviso" data-testid="receita-aviso">
        {textos.aviso}
      </p>
      {semEstimativa > 0 ? (
        <p className="aviso" data-testid="receita-sem-data">
          {semEstimativa === 1
            ? textos.semDataNaContaUm
            : preencher(textos.semDataNaConta, { n: formatarInteiro(semEstimativa) })}
        </p>
      ) : null}
      <div className="campo">
        <label htmlFor="comissao">{textos.campo}</label>
        <input
          id="comissao"
          data-testid="comissao"
          type="number"
          inputMode="decimal"
          min="0"
          max="100"
          step="0.1"
          value={comissao}
          onChange={(e) => mudarComissao(e.target.value)}
        />
      </div>
      {valida ? (
        <p className="receita__comissao" data-testid="comissao-total">
          {quaseNada(valorComissao)
            ? textos.comissaoQuaseNada
            : preencher(textos.comissao, { valor: formatarInteiro(valorComissao) })}
        </p>
      ) : null}
    </section>
  );
}

/** Os grupos na ordem da tela. Sem `aoEncaminhar`, a lista é só de leitura. */
export function Grupos({
  fila,
  base,
  aoEncaminhar,
  aoEncaminharLote,
}: {
  fila: Fila;
  base: Base;
  aoEncaminhar?: (i: ItemFila) => void;
  aoEncaminharLote?: (itens: readonly ItemFila[]) => void;
}) {
  const porGrupo = useMemo(() => agruparPorGrupo(fila), [fila]);
  return (
    <div className="blocos">
      {ORDEM.filter(
        // Siga promovido: os negócios dele aparecem no Foque, e o grupo vazio não aparece
        (g) => !(g === 'siga_no_ritmo' && fila.promovidos > 0 && porGrupo[g].length === 0),
      ).map((g) => (
        <GrupoDaFila
          key={g}
          grupo={g}
          itens={porGrupo[g]}
          base={base}
          {...(aoEncaminhar ? { aoEncaminhar } : {})}
          {...(aoEncaminharLote ? { aoEncaminharLote } : {})}
        />
      ))}
    </div>
  );
}

/** Encaminhado = a última decisão do vendedor foi aceitar o encaminhamento para nutrição. */
function encaminhado(i: ItemFila): boolean {
  return i.decisao?.acao === 'encaminhar_para_nutricao' && i.decisao.aceita;
}

/**
 * "Encaminhar os N" com confirmação na própria tela (sem janela do navegador): o primeiro clique
 * pergunta "Encaminhar N negócios para nutrição?"; só "Sim, encaminhar" grava.
 */
function LoteDaNutricao({
  pendentes,
  base,
  aoEncaminharLote,
}: {
  pendentes: readonly ItemFila[];
  base: Base;
  aoEncaminharLote: (itens: readonly ItemFila[]) => void;
}) {
  const t = base.politica.textos.nutricao;
  const [confirmando, setConfirmando] = useState(false);
  const n = formatarInteiro(pendentes.length);
  if (pendentes.length === 0) return null;
  if (!confirmando) {
    return (
      <button
        type="button"
        className="botao ls-t-colors"
        data-testid="nutricao-lote"
        onClick={() => setConfirmando(true)}
      >
        {preencher(t.botao, { n })}
      </button>
    );
  }
  return (
    <div className="confirmacao" role="group" aria-labelledby="nutricao-lote-pergunta">
      <p id="nutricao-lote-pergunta" data-testid="nutricao-lote-pergunta">
        {preencher(t.pergunta, { n })}
      </p>
      <div className="acoes">
        <button
          type="button"
          className="botao ls-t-colors"
          data-testid="nutricao-lote-confirmar"
          onClick={() => {
            setConfirmando(false);
            aoEncaminharLote(pendentes);
          }}
        >
          {t.confirmar}
        </button>
        <button
          type="button"
          className="botao botao--ghost ls-t-colors"
          data-testid="nutricao-lote-cancelar"
          onClick={() => setConfirmando(false)}
        >
          {t.cancelar}
        </button>
      </div>
    </div>
  );
}

function GrupoDaFila({
  grupo,
  itens,
  base,
  aoEncaminhar,
  aoEncaminharLote,
}: {
  grupo: Grupo;
  itens: ItemFila[];
  base: Base;
  aoEncaminhar?: (i: ItemFila) => void;
  aoEncaminharLote?: (itens: readonly ItemFila[]) => void;
}) {
  const texto = base.textos.grupos[grupo];
  const textosNutricao = base.politica.textos.nutricao;
  const [quantos, setQuantos] = useState(POR_VEZ);
  // a Nutrição começa recolhida: só a contagem, até o vendedor pedir para ver
  const [aberto, setAberto] = useState(grupo !== 'nutricao');
  const slug = SLUG[grupo];
  const tituloId = 'titulo-' + slug;
  const pendentes = useMemo(() => itens.filter((i) => !encaminhado(i)), [itens]);
  return (
    <section
      className={'bloco bloco--' + grupo}
      data-testid={testidDoGrupo(grupo)}
      aria-labelledby={tituloId}
    >
      <header className="bloco__cabeca">
        <h2 className="bloco__titulo" id={tituloId}>
          {texto.titulo}
        </h2>
        <span
          className="contador"
          data-testid={'contador-' + slug}
          aria-label={itens.length + ' negócios'}
        >
          {itens.length}
        </span>
      </header>
      <p className="bloco__porque">{texto.subtitulo}</p>
      {grupo === 'nutricao' ? <p className="bloco__nota">{base.textos.avisos.nutricao}</p> : null}
      {grupo === 'nutricao' && itens.length > 0 ? (
        <div className="acoes">
          <button
            type="button"
            className="botao botao--ghost ls-t-colors"
            data-testid="nutricao-alternar"
            aria-expanded={aberto}
            onClick={() => setAberto((a) => !a)}
          >
            {aberto
              ? textosNutricao.recolher
              : preencher(textosNutricao.mostrar, { n: formatarInteiro(itens.length) })}
          </button>
          {aoEncaminharLote ? (
            <LoteDaNutricao pendentes={pendentes} base={base} aoEncaminharLote={aoEncaminharLote} />
          ) : null}
        </div>
      ) : null}
      {itens.length === 0 ? (
        <p className="vazio">{texto.vazio}</p>
      ) : !aberto ? null : (
        <div {...(grupo === 'nutricao' ? { 'data-testid': 'lista-nutricao' } : {})}>
          <ul className="lista">
            {itens.slice(0, quantos).map((i) => (
              <ItemDaFila
                key={i.deal.id}
                item={i}
                rotuloBotaoNutricao={base.textos.grupos.nutricao.acao}
                rotuloPorque={base.politica.textos.score.verPorque}
                textosNutricao={textosNutricao}
                {...(aoEncaminhar ? { aoEncaminhar } : {})}
              />
            ))}
          </ul>
          {itens.length > quantos ? (
            <button
              type="button"
              className="botao botao--ghost mais"
              onClick={() => setQuantos((q) => q + POR_VEZ)}
            >
              Mostrar mais {Math.min(POR_VEZ, itens.length - quantos)} de {itens.length - quantos}
            </button>
          ) : null}
        </div>
      )}
    </section>
  );
}
