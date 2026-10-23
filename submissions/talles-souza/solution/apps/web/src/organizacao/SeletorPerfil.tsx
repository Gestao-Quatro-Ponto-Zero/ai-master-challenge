import type { Vendedor } from '@lead-scorer/dominio/organizacao';
import { GRUPOS, type Grupo } from '@lead-scorer/dominio/priorizacao';
import { useEffect, useId, useRef, useState, type KeyboardEvent } from 'react';

/** Os vendedores agrupados por escritório e manager, na ordem de nome de cada nível. */
export function agruparTime(
  vendedores: readonly Vendedor[],
): { rotulo: string; vendedores: Vendedor[] }[] {
  const grupos = new Map<string, Vendedor[]>();
  const ordenados = [...vendedores].sort(
    (a, b) =>
      a.regiao.localeCompare(b.regiao, 'pt-BR') ||
      a.manager.localeCompare(b.manager, 'pt-BR') ||
      a.nome.localeCompare(b.nome, 'pt-BR'),
  );
  for (const v of ordenados) {
    const rotulo = v.regiao + ' · ' + v.manager;
    grupos.set(rotulo, [...(grupos.get(rotulo) ?? []), v]);
  }
  return [...grupos.entries()].map(([rotulo, vs]) => ({ rotulo, vendedores: vs }));
}

/**
 * Quantos abertos o vendedor tem em cada grupo, na ordem e na cor dos grupos da tela. A cor é
 * reforço: o leitor de tela ouve "Foque agora: 2", e o título mostra o nome ao passar o mouse.
 */
function Contagens({ vendedor, titulos }: { vendedor: Vendedor; titulos: Record<Grupo, string> }) {
  const grupos = vendedor.grupos;
  if (!grupos) return null;
  return (
    <span className="contagens" data-testid="seletor-contagens">
      {GRUPOS.map((g) => (
        <span
          key={g}
          className={'contagem contagem--' + g + (grupos[g] === 0 ? ' contagem--zero' : '')}
          title={titulos[g]}
          data-grupo={g}
        >
          <span className="contagem__ponto" aria-hidden="true" />
          <span aria-hidden="true">{grupos[g]}</span>
          <span className="sr-only">
            {titulos[g]}: {grupos[g]}
          </span>
        </span>
      ))}
    </span>
  );
}

/**
 * "Quem é você?": o time inteiro, agrupado por escritório e manager (inclusive quem não tem
 * negócio), cada um com quantos abertos tem em cada grupo, na cor do grupo. Diz de quem é a
 * lista. Não é login; qualquer um pode escolher qualquer nome, e a escolha fica só neste
 * navegador. É uma lista própria (botão + listbox) porque o `<select>` nativo não mostra cor;
 * teclado: setas, Home/End, Enter ou espaço escolhe, Esc fecha.
 */
export function SeletorPerfil({
  vendedores,
  valor,
  aoEscolher,
  rotulo,
  escolha,
  titulos,
}: {
  vendedores: readonly Vendedor[];
  valor: string | null;
  aoEscolher: (nome: string) => void;
  /** "Quem é você?" (dos textos da política). */
  rotulo: string;
  /** O texto do botão antes da primeira escolha. */
  escolha: string;
  /** O título de cada grupo (dos textos da tela), para o leitor de tela e o título das contagens. */
  titulos: Record<Grupo, string>;
}) {
  const [aberto, setAberto] = useState(false);
  const [ativo, setAtivo] = useState<string | null>(null);
  const raiz = useRef<HTMLDivElement>(null);
  const botao = useRef<HTMLButtonElement>(null);
  const lista = useRef<HTMLUListElement>(null);
  const id = useId();
  const grupos = agruparTime(vendedores);
  const nomes = grupos.flatMap((g) => g.vendedores.map((v) => v.nome));
  const atual = vendedores.find((v) => v.nome === valor) ?? null;
  const idOpcao = (nome: string) => id + '-opcao-' + nomes.indexOf(nome);
  const idAtivo = ativo === null ? null : idOpcao(ativo);

  useEffect(() => {
    if (!aberto) return;
    lista.current?.focus();
    const fora = (e: MouseEvent) => {
      if (!raiz.current?.contains(e.target as Node)) setAberto(false);
    };
    document.addEventListener('mousedown', fora);
    return () => document.removeEventListener('mousedown', fora);
  }, [aberto]);

  useEffect(() => {
    if (aberto && idAtivo) document.getElementById(idAtivo)?.scrollIntoView?.({ block: 'nearest' });
  }, [aberto, idAtivo]);

  function abrir() {
    setAtivo(valor ?? nomes[0] ?? null);
    setAberto(true);
  }

  function fechar() {
    setAberto(false);
    botao.current?.focus();
  }

  function escolher(nome: string) {
    aoEscolher(nome);
    fechar();
  }

  function mover(passo: number | 'inicio' | 'fim') {
    if (nomes.length === 0) return;
    const i = ativo === null ? -1 : nomes.indexOf(ativo);
    const j =
      passo === 'inicio'
        ? 0
        : passo === 'fim'
          ? nomes.length - 1
          : Math.min(nomes.length - 1, Math.max(0, i + passo));
    setAtivo(nomes[j] ?? null);
  }

  function teclaNoBotao(e: KeyboardEvent<HTMLButtonElement>) {
    if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(e.key)) {
      e.preventDefault();
      abrir();
    }
  }

  function teclaNaLista(e: KeyboardEvent<HTMLUListElement>) {
    if (e.key === 'Tab') {
      setAberto(false);
      return;
    }
    const escolherAtivo = () => (ativo ? escolher(ativo) : fechar());
    const acoes: Record<string, () => void> = {
      ArrowDown: () => mover(1),
      ArrowUp: () => mover(-1),
      Home: () => mover('inicio'),
      End: () => mover('fim'),
      Enter: escolherAtivo,
      ' ': escolherAtivo,
      Escape: fechar,
    };
    const acao = acoes[e.key];
    if (!acao) return;
    e.preventDefault();
    acao();
  }

  return (
    <div className="seletor" ref={raiz}>
      <span id={id + '-rotulo'}>{rotulo}</span>
      <button
        ref={botao}
        type="button"
        id={id + '-botao'}
        className="seletor__botao"
        data-testid="seletor-perfil"
        data-valor={valor ?? ''}
        aria-haspopup="listbox"
        aria-expanded={aberto}
        aria-labelledby={id + '-rotulo ' + id + '-botao'}
        onClick={() => (aberto ? fechar() : abrir())}
        onKeyDown={teclaNoBotao}
      >
        {atual ? (
          <>
            <span className="seletor__nome">
              {atual.nome} ({atual.abertos} abertos)
            </span>
            <Contagens vendedor={atual} titulos={titulos} />
          </>
        ) : (
          <span className="seletor__nome">{escolha}</span>
        )}
        <span className="seletor__seta" aria-hidden="true">
          ▾
        </span>
      </button>
      {aberto ? (
        <ul
          ref={lista}
          role="listbox"
          tabIndex={-1}
          className="seletor__lista"
          data-testid="seletor-perfil-lista"
          aria-labelledby={id + '-rotulo'}
          {...(idAtivo ? { 'aria-activedescendant': idAtivo } : {})}
          onKeyDown={teclaNaLista}
        >
          {grupos.map((g) => (
            <li key={g.rotulo} role="group" aria-label={g.rotulo}>
              <span className="seletor__grupo" aria-hidden="true">
                {g.rotulo}
              </span>
              <ul role="none">
                {g.vendedores.map((v) => (
                  <li
                    key={v.nome}
                    id={idOpcao(v.nome)}
                    role="option"
                    aria-selected={v.nome === valor}
                    data-valor={v.nome}
                    className={
                      'seletor__opcao' + (v.nome === ativo ? ' seletor__opcao--ativa' : '')
                    }
                    onMouseDown={(e) => e.preventDefault()}
                    onMouseEnter={() => setAtivo(v.nome)}
                    onClick={() => escolher(v.nome)}
                  >
                    <span className="seletor__nome">
                      {v.nome} ({v.abertos} abertos)
                    </span>
                    <Contagens vendedor={v} titulos={titulos} />
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      ) : null}
      <span className="leitura">Escolher o nome não é login: só diz de quem é a lista.</span>
    </div>
  );
}
