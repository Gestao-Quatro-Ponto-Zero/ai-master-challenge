import { useRef, useState } from "react";
import { AgeRuler, BUCKETS, BUCKET_ORDER, DealName, Empty, Score } from "../components";
import { PRIORITY, dealInScope, recentlyClosed, useApp, useScopedOpen, type DecisionKind } from "../data";
import { int, money, pct, plural, shortDateTime } from "../format";
import { link } from "../router";
import type { Bucket, OpenDeal } from "../types";

type SortKey = "score" | "age" | "win_prob" | "ev_soon" | "price" | "agent";

const COLUMNS: [SortKey, string][] = [
  ["score", "Score (ganhar em 30d)"],
  ["agent", "Vendedor"],
  ["age", "Idade"],
  ["win_prob", "Ganhar, sem prazo"],
  ["ev_soon", "Receita esperada (30d)"],
  ["price", "Valor"],
];

const PAGE = 100;

export function Pipeline({ query }: { query: URLSearchParams }) {
  const { model, decisions, filters } = useApp();
  const scoped = useScopedOpen();
  const fila = query.get("fila") as Bucket | null;
  const semConta = query.get("semconta") === "1";
  const conflito = query.get("conflito") === "1";
  const board = query.get("ver") === "quadro";
  const encerrados = query.get("encerrados") === "1";
  const closed = recentlyClosed(model, filters, decisions);
  const [search, setSearch] = useState(() => query.get("busca") ?? "");
  // A ordem padrão segue a fila: Decidir e Prospectar não têm receita esperada
  // (ev_soon = 0), então ordenar por ela deixaria a lista na ordem do arquivo.
  // O PRIORITY já diz que essas duas filas se ordenam por valor de lista.
  const [sortOverride, setSort] = useState<{ key: SortKey; dir: 1 | -1 } | null>(null);
  const defaultSort: { key: SortKey; dir: 1 | -1 } = {
    key: fila === "decidir" || fila === "prospectar" ? "price" : "ev_soon",
    dir: -1,
  };
  const sort = sortOverride ?? defaultSort;

  const href = (changes: Record<string, string | null>) => {
    const q = new URLSearchParams(query);
    for (const [k, v] of Object.entries(changes)) v ? q.set(k, v) : q.delete(k);
    const s = q.toString();
    return link("pipeline") + (s ? `?${s}` : "");
  };

  const needle = search.trim().toLowerCase();
  const conflictCount = scoped.filter((d) => (d.conflicts?.length ?? 0) > 0).length;
  const visible = scoped.filter(
    (d) =>
      (!fila || d.bucket === fila) &&
      (!semConta || !d.account) &&
      (!conflito || (d.conflicts?.length ?? 0) > 0) &&
      (!needle || [d.account, d.product, d.agent, d.id].some((v) => v?.toLowerCase().includes(needle))),
  );
  const decidedCount = model.open.filter((d) => decisions[d.id] && dealInScope(d, filters)).length;

  return (
    <div>
      <header className="page-head">
        <h1>Pipeline</h1>
        {encerrados ? (
          <p className="lede">
            {plural(closed.length, "deal encerrado", "deals encerrados")} como perdido na última semana, no seu recorte. Esta lista serve para revisar se o motivo ainda vale; nada aqui pede ação.
          </p>
        ) : (
          <p className="lede">
            {int(visible.length)} de {int(scoped.length)} deals abertos no seu recorte.
            {decidedCount > 0 && ` ${plural(decidedCount, "deal já decidido fica", "deals já decididos ficam")} fora desta lista.`}
          </p>
        )}
      </header>

      <div className="toolbar">
        <nav className="tabs" aria-label="Filas">
          <a href={href({ encerrados: null, fila: null })} aria-current={!fila && !encerrados ? "page" : undefined}>Todas</a>
          {BUCKET_ORDER.map((b) => (
            <a key={b} href={href({ encerrados: null, fila: b })} aria-current={fila === b ? "page" : undefined} className={`tab-${b}`}>
              {BUCKETS[b].label} <span className="count">{int(scoped.filter((d) => d.bucket === b).length)}</span>
            </a>
          ))}
          {closed.length > 0 && (
            <a
              href={href({ encerrados: encerrados ? null : "1", fila: null })}
              aria-current={encerrados ? "page" : undefined}
              className="tab-encerrados"
              title="Deals que você encerrou como perdido na última semana, para revisar o motivo"
            >
              Encerrados na semana <span className="count">{int(closed.length)}</span>
            </a>
          )}
        </nav>
        <input
          type="search"
          placeholder="Buscar conta, produto ou vendedor"
          aria-label="Buscar deals"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <a className="btn-link" href={href({ semconta: semConta ? null : "1" })}>
          {semConta ? "Mostrar todos" : "Só sem conta"}
        </a>
        <a className={`btn-link${conflito ? " is-active" : ""}`} href={href({ conflito: conflito ? null : "1" })}
          title="Deals em que outro vendedor fechou o mesmo produto na mesma conta depois deste deal abrir">
          {conflito ? "Mostrar todos" : `Com conflito (${int(conflictCount)})`}
        </a>
        <a className="btn-link" href={href({ ver: board ? null : "quadro" })}>
          {board ? "Ver em lista" : "Ver em quadro"}
        </a>
      </div>

      {encerrados ? (
        closed.length === 0 ? (
          <Empty>Nenhum deal encerrado na última semana no seu recorte.</Empty>
        ) : (
          <ClosedTable deals={closed} />
        )
      ) : visible.length === 0 ? (
        <Empty>Nenhum deal com esses filtros. Limpe a busca ou troque de fila.</Empty>
      ) : board ? (
        <Board deals={visible} />
      ) : (
        <DealTable deals={visible} sort={sort} setSort={(s) => setSort(s)} bulkDecide={fila === "decidir"} />
      )}
    </div>
  );
}

/** Aba de higiene: os deals que o vendedor encerrou como perdido na última
    semana. Colunas enxutas de propósito (não é a fila de decisão) — importa o
    que foi fechado, quando e por quê, pra reabrir com contexto se o motivo
    ainda valer. */
function ClosedTable({ deals }: { deals: OpenDeal[] }) {
  const { decisions } = useApp();
  return (
    <>
      <div className="table-wrap">
        <table className="deals">
          <thead>
            <tr>
              <th scope="col" className="cell-pin">Deal</th>
              <th scope="col">Vendedor</th>
              <th scope="col">Encerrado em</th>
              <th scope="col">Nota da decisão</th>
            </tr>
          </thead>
          <tbody>
            {deals.map((d) => {
              const dec = decisions[d.id];
              return (
                <tr key={d.id} className="row-encerrado">
                  <td className="cell-pin">
                    <a href={link("deal", d.id)} className="cell-deal"><DealName deal={d} /></a>
                  </td>
                  <td>{d.agent}</td>
                  <td>{dec ? shortDateTime(dec.at) : "—"}</td>
                  <td className="cell-note">
                    {dec?.note ? <span>{dec.note}</span> : <span className="muted">Sem nota</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="context">
        Esses deals voltam pra fila se você desfizer a decisão. Revisar enquanto está fresco evita
        "encerrado por engano" virar perda silenciosa.
      </p>
    </>
  );
}

function sortValue(d: OpenDeal, key: SortKey): number | string {
  if (key === "agent") return d.agent;
  if (key === "age") return d.age ?? -1;
  if (key === "win_prob") return d.win_prob ?? -1;
  if (key === "score") return d.score ?? -1;
  return d[key];
}

function DealTable(props: {
  deals: OpenDeal[];
  sort: { key: SortKey; dir: 1 | -1 };
  setSort: (s: { key: SortKey; dir: 1 | -1 }) => void;
  /** Decidir é a única fila onde nenhuma característica distingue um deal do outro
      (ver os testes de significância no README) — revisar 1.300 um a um não muda
      a decisão, então aqui, e só aqui, dá pra decidir em lote. */
  bulkDecide?: boolean;
}) {
  const { model, decide } = useApp();
  const { sort, bulkDecide } = props;
  const tableWrap = useRef<HTMLDivElement>(null);
  // Paginação por clique, não scroll infinito: cada página mostra PAGE deals e o
  // controle leva de volta ao topo da tabela — um gesto explícito, não um
  // "Mostrar mais" que cresce a lista sem fim.
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [confirming, setConfirming] = useState<DecisionKind | null>(null);
  const [lastBulk, setLastBulk] = useState<{ kind: DecisionKind; ids: string[] } | null>(null);
  // desfazer em três modos (mesmo padrão discreto do undo por deal, sem timer)
  const [undoOpen, setUndoOpen] = useState(false);
  const [undoSel, setUndoSel] = useState<Set<string>>(new Set());
  const [undoNames, setUndoNames] = useState("");
  const rows = [...props.deals].sort((a, b) => {
    const va = sortValue(a, sort.key), vb = sortValue(b, sort.key);
    return (va < vb ? -1 : va > vb ? 1 : b.ev_soon - a.ev_soon) * sort.dir;
  });
  const pageCount = Math.max(1, Math.ceil(rows.length / PAGE));
  const clamped = Math.min(page, pageCount - 1);
  const go = (p: number) => {
    setPage(Math.min(Math.max(p, 0), pageCount - 1));
    // leva o olhar pra primeira linha da nova página, não pra onde o scroll estava
    tableWrap.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  const start = clamped * PAGE;
  const visible = rows.slice(start, start + PAGE);
  const allSelected = bulkDecide && visible.length > 0 && visible.every((d) => selected.has(d.id));
  const toggleAll = () => setSelected(allSelected ? new Set() : new Set(visible.map((d) => d.id)));
  const suggestedClose = visible.filter((d) => d.suggested_action === "encerrar");
  const selectSuggestedClose = () => setSelected(new Set(suggestedClose.map((d) => d.id)));
  const toggleOne = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  const confirmBulk = () => {
    if (!confirming) return;
    const ids = [...selected];
    ids.forEach((id) => decide(id, confirming));
    setLastBulk({ kind: confirming, ids });
    setUndoSel(new Set(ids)); // por padrão desfaz-se tudo; o painel deixa estreitar
    setUndoNames("");
    setUndoOpen(false);
    setSelected(new Set());
    setConfirming(null);
  };
  const undoDeals: OpenDeal[] = lastBulk
    ? lastBulk.ids
        .map((id) => model.byId.get(id))
        .filter((d): d is OpenDeal => !!d && (d.stage === "Prospecting" || d.stage === "Engaging"))
    : [];
  /** Chama decide(id, null) pra cada id e limpa o estado de undo. */
  const setDecisionsOnUndo = (ids: Iterable<string>) => {
    for (const id of ids) decide(id, null);
    setLastBulk(null);
    setUndoOpen(false);
  };
  const undoAll = () => lastBulk && setDecisionsOnUndo(lastBulk.ids);
  const undoSelected = () => {
    if (undoSel.size === 0) return;
    setDecisionsOnUndo(undoSel);
  };
  const toggleUndo = (id: string) =>
    setUndoSel((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  // "ir por pesquisa": colar nomes/contas separadas por vírgula seleciona só esses
  const applyUndoNames = () => {
    if (!lastBulk) return;
    const needles = undoNames.split(/[\n,;]+/).map((s) => s.trim().toLowerCase()).filter(Boolean);
    if (needles.length === 0) return;
    setUndoSel((prev) => {
      const next = new Set(prev);
      for (const id of lastBulk.ids) {
        const d = model.byId.get(id);
        if (!d || (d.stage !== "Prospecting" && d.stage !== "Engaging")) continue;
        const hay = `${d.account ?? ""} ${d.product} ${d.id}`.toLowerCase();
        if (needles.some((n) => hay.includes(n))) next.add(id);
      }
      return next;
    });
    setUndoNames("");
  };

  return (
    <>
      {bulkDecide && visible.length > 0 && (
        <div className="bulk-bar">
          {confirming ? (
            <>
              <span>
                Confirma {confirming === "encerrado" ? "encerrar" : "requalificar"}{" "}
                {plural(selected.size, "deal", "deals")}?
              </span>
              <button className="btn" onClick={confirmBulk}>Sim, confirmar</button>
              <button className="btn-link" onClick={() => setConfirming(null)}>Cancelar</button>
            </>
          ) : selected.size > 0 ? (
            <>
              <span>{plural(selected.size, "selecionado", "selecionados")}</span>
              <button className="btn" onClick={() => setConfirming("requalificado")}>Requalifiquei</button>
              <button className="btn btn-quiet" onClick={() => setConfirming("encerrado")}>Encerrar como perdido</button>
              <button className="btn-link" onClick={() => setSelected(new Set())}>Limpar seleção</button>
            </>
          ) : (
            <>
              <span className="muted">Marque os deals abaixo para requalificar ou encerrar vários de uma vez.</span>
              {suggestedClose.length > 0 && (
                <button className="btn-link" onClick={selectSuggestedClose}>
                  Selecionar {plural(suggestedClose.length, "sugerido", "sugeridos")} para encerrar
                </button>
              )}
            </>
          )}
        </div>
      )}
      {lastBulk && (
        <div className="bulk-undo">
          <div className="bulk-undo-bar">
            <span>
              {plural(lastBulk.ids.length, "deal", "deals")}{" "}
              {lastBulk.kind === "encerrado" ? "encerrado(s) como perdido" : "requalificado(s)"}.
            </span>
            <button className="btn-link" onClick={undoAll}>Desfazer todos</button>
            <button
              className="btn-link" onClick={() => setUndoOpen((v) => !v)} aria-expanded={undoOpen}
              aria-controls="bulk-undo-panel"
            >
              {undoOpen ? "Fechar seleção" : "Escolher quais desfazer"}
            </button>
          </div>
          {undoOpen && (
            <div className="bulk-undo-panel" id="bulk-undo-panel">
              <div className="bulk-undo-names">
                <input
                  type="text" value={undoNames} placeholder="Cole nomes ou contas, separados por vírgula, para desfazer só esses"
                  aria-label="Nomes de deals para desfazer"
                  onChange={(e) => setUndoNames(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); applyUndoNames(); } }}
                />
                <button className="btn-link" onClick={applyUndoNames}>Adicionar à seleção</button>
              </div>
              <ul className="bulk-undo-list">
                {undoDeals.map((d) => (
                  <li key={d.id}>
                    <label>
                      <input
                        type="checkbox" checked={undoSel.has(d.id)} onChange={() => toggleUndo(d.id)}
                        aria-label={`Desfazer ${d.account ?? "deal sem conta"}, ${d.product}`}
                      />
                      <DealName deal={d} />
                    </label>
                  </li>
                ))}
              </ul>
              <div className="bulk-undo-actions">
                <button className="btn" onClick={undoSelected} disabled={undoSel.size === 0}>
                  {undoSel.size === lastBulk.ids.length
                    ? "Desfazer todos"
                    : `Desfazer ${int(undoSel.size)} ${undoSel.size === 1 ? "deal" : "deals"}`}
                </button>
                <button className="btn-link" onClick={() => setUndoSel(new Set(lastBulk.ids))}>Redefinir todos</button>
                <button className="btn-link" onClick={() => setUndoSel(new Set())}>Deselecionar tudo</button>
              </div>
            </div>
          )}
        </div>
      )}
      <div className="table-wrap" ref={tableWrap}>
        <table className="deals">
          <thead>
            <tr>
              {bulkDecide && (
                <th scope="col" className="cell-check">
                  <input type="checkbox" checked={allSelected} onChange={toggleAll} aria-label="Selecionar todos os visíveis" />
                </th>
              )}
              <th scope="col" className="cell-pin">Deal</th>
              {COLUMNS.map(([key, label]) => (
                <th key={key} scope="col" aria-sort={sort.key === key ? (sort.dir === 1 ? "ascending" : "descending") : undefined}>
                  <button onClick={() => props.setSort({ key, dir: sort.key === key ? (-sort.dir as 1 | -1) : -1 })}>
                    {label}
                  </button>
                </th>
              ))}
              <th scope="col">Próxima ação</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((d) => (
              <tr key={d.id} className={`row-${d.bucket}${selected.has(d.id) ? " row-selected" : ""}`}>
                {bulkDecide && (
                  <td className="cell-check">
                    <input
                      type="checkbox" checked={selected.has(d.id)} onChange={() => toggleOne(d.id)}
                      aria-label={`Selecionar ${d.account ?? "deal sem conta"}, ${d.product}`}
                    />
                  </td>
                )}
                <td className="cell-pin">
                  <a href={link("deal", d.id)} className="cell-deal">
                    <DealName deal={d} />
                    {d.conflicts && d.conflicts.length > 0 && (
                      <span className="tag-conflict" title={`${d.conflicts.length === 1 ? "1 fechamento" : `${d.conflicts.length} fechamentos`} do mesmo produto nesta conta por outro vendedor depois deste deal abrir`}>
                        conflito
                      </span>
                    )}
                  </a>
                </td>
                <td><Score deal={d} showTier /></td>
                <td>{d.agent}</td>
                <td className="cell-ruler"><AgeRuler age={d.age} meta={model.meta} /></td>
                <td className="num">{pct(d.win_prob)}</td>
                <td className="num">{money(d.ev_soon)}</td>
                <td className="num">{money(d.price)}</td>
                <td className="cell-action">
                  <a href={link("deal", d.id)} title={d.action}>
                    <span>{d.action}</span>
                    <svg viewBox="0 0 14 14" aria-hidden="true"><path d="M4 10 10 4M10 4H5.5M10 4v4.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <nav className="pager" aria-label="Paginação da lista">
        <span className="pager-info">
          {int(start + 1)}–{int(start + visible.length)} de {int(rows.length)}
        </span>
        <button className="btn btn-quiet" disabled={clamped === 0} onClick={() => go(clamped - 1)} aria-label="Página anterior">
          <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" /></svg>
          Anterior
        </button>
        <span className="pager-page">
          Página {clamped + 1} de {pageCount}
        </span>
        <button className="btn btn-quiet" disabled={clamped >= pageCount - 1} onClick={() => go(clamped + 1)} aria-label="Próxima página">
          Próxima
          <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </button>
      </nav>
    </>
  );
}

const BOARD_LIMIT = 30;

function Board({ deals }: { deals: OpenDeal[] }) {
  const { model } = useApp();
  return (
    <div className="board">
      {BUCKET_ORDER.map((b) => {
        const col = deals.filter((d) => d.bucket === b).sort(PRIORITY[b]);
        return (
          <section key={b} className={`board-col col-${b}`}>
            <h2>
              {BUCKETS[b].label} <span className="count">{int(col.length)}</span>
            </h2>
            <p className="board-total">
              {b === "decidir" || b === "prospectar"
                ? `${money(col.reduce((s, d) => s + d.price, 0))} declarados`
                : `${money(col.reduce((s, d) => s + d.ev_soon, 0))} esperados em 30 dias`}
            </p>
            <p className="queue-hint">{BUCKETS[b].hint}</p>
            {col.slice(0, BOARD_LIMIT).map((d) => (
              <a key={d.id} className="card" href={link("deal", d.id)}>
                <span className="card-top">
                  <span className="card-name"><DealName deal={d} /></span>
                  <Score deal={d} />
                </span>
                <AgeRuler age={d.age} meta={model.meta} />
                <span className="card-sub">
                  {money(d.price)}, {d.agent}
                  {d.conflicts && d.conflicts.length > 0 && <span className="tag-conflict">conflito</span>}
                </span>
              </a>
            ))}
            {col.length > BOARD_LIMIT && (
              <a className="btn-link" href={`${link("pipeline")}?fila=${b}`}>Ver todos os {int(col.length)} em lista</a>
            )}
          </section>
        );
      })}
    </div>
  );
}
