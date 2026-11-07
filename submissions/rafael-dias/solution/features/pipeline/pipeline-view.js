import Icon from "../../components/ui/icon";
import { SectionTitle, Empty } from "../../components/ui/primitives";
import { matches } from "../../lib/format.mjs";
import { STAGES } from "../../lib/workflow.mjs";
import DealCard from "../opportunities/deal-card";
export default function PipelineView({
  mine,
  query,
  queue,
  limit,
  dropTarget,
  setQuery,
  setQueue,
  setLimit,
  setDropTarget,
  setDragged,
  handleDrop,
  openDeal,
}) {
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">DO PRIMEIRO CONTATO À VENDA</div>
          <h1>
            Seu pipeline, em movimento<span className="gold">.</span>
          </h1>
          <p>
            Abra uma oportunidade, execute o próximo passo e registre o avanço.
          </p>
        </div>
        <span className="small-tag">
          {mine.length} oportunidades na carteira
        </span>
      </div>
      <div className="pipeline-toolbar">
        <label className="search-field">
          <Icon name="search" size={17} />
          <input
            aria-label="Buscar na carteira"
            placeholder="Buscar conta, produto ou oportunidade"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setLimit(20);
            }}
          />
        </label>
        <div className="segmented">
          {[
            ["focus", "Pipeline"],
            ["missing", "Completar cadastro"],
            ["all", "Toda a carteira"],
          ].map(([id, label]) => (
            <button
              aria-pressed={queue === id}
              className={queue === id ? "active" : ""}
              key={id}
              onClick={() => {
                setQueue(id);
                setLimit(20);
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      {queue === "focus" ? (
        <div className="kanban">
          {STAGES.map((s) => {
            const group = mine
              .filter((d) => d.status === s.id && matches(d, query))
              .sort((a, b) => b.score - a.score);
            return (
              <section
                className={
                  "kanban-column " +
                  s.id +
                  (dropTarget === s.id ? " drop-active" : "")
                }
                key={s.id}
                onDragOver={(e) => {
                  e.preventDefault();
                  e.dataTransfer.dropEffect = "move";
                  setDropTarget(s.id);
                }}
                onDragLeave={(e) => {
                  if (!e.currentTarget.contains(e.relatedTarget))
                    setDropTarget(null);
                }}
                onDrop={(e) => handleDrop(e, s.id)}
              >
                <header>
                  <span className="column-dot" />
                  <h2>{s.label}</h2>
                  <span>{group.length}</span>
                </header>
                <div className="column-cards">
                  {group.slice(0, limit).map((d) => (
                    <DealCard
                      key={d.opportunity_id}
                      deal={d}
                      onClick={() => openDeal(d.opportunity_id)}
                      onDragStart={(e) => {
                        e.dataTransfer.setData("text/plain", d.opportunity_id);
                        e.dataTransfer.effectAllowed = "move";
                        setDragged(d.opportunity_id);
                      }}
                      onDragEnd={() => {
                        setDragged(null);
                        setDropTarget(null);
                      }}
                    />
                  ))}
                  {!group.length && (
                    <div className="column-empty">
                      {s.id === "qualified"
                        ? "Confirme necessidade, decisor e prazo para gerar seu primeiro SQL."
                        : "Os avanços registrados aparecerão aqui."}
                    </div>
                  )}
                  {group.length > limit && (
                    <button
                      className="button secondary"
                      onClick={() => setLimit(limit + 20)}
                    >
                      Carregar mais {Math.min(20, group.length - limit)}
                    </button>
                  )}
                </div>
              </section>
            );
          })}
        </div>
      ) : (
        <section className="panel">
          <SectionTitle
            title={
              queue === "missing"
                ? "Identificar antes de abordar"
                : "Sua carteira completa"
            }
            subtitle="O score não substitui a confirmação comercial."
          />
          <div className="portfolio-grid">
            {mine
              .filter(
                (d) => (queue !== "missing" || !d.account) && matches(d, query),
              )
              .sort((a, b) => b.score - a.score)
              .slice(0, limit)
              .map((d) => (
                <DealCard
                  key={d.opportunity_id}
                  deal={d}
                  onClick={() => openDeal(d.opportunity_id)}
                />
              ))}
          </div>
          {!mine.some(
            (d) => (queue !== "missing" || !d.account) && matches(d, query),
          ) && (
            <Empty
              title="Nenhuma oportunidade encontrada"
              text="Tente outro termo de busca ou outra fila."
            />
          )}
          {mine.filter(
            (d) => (queue !== "missing" || !d.account) && matches(d, query),
          ).length > limit && (
            <button
              className="button secondary load-more"
              onClick={() => setLimit(limit + 20)}
            >
              Carregar mais oportunidades
            </button>
          )}
        </section>
      )}
    </>
  );
}
