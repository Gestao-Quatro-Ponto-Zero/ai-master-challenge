import FocusQueue from "./focus-queue";
import Icon from "../../components/ui/icon";
import { Kpi, SectionTitle } from "../../components/ui/primitives";
import { dateLabel } from "../../lib/format.mjs";
import { STAGES } from "../../lib/workflow.mjs";
export default function TodayView({
  agent,
  open,
  top,
  due,
  qualified,
  contactsToday,
  agenda,
  mine,
  progress,
  setSelected,
  setView,
  setQueue,
}) {
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">SEU DIA COMEÇA COM DIREÇÃO</div>
          <h1>
            Vamos avançar, {agent.split(" ")[0]}
            <span className="gold">.</span>
          </h1>
          <p>
            Você tem <strong>{open.length} oportunidades abertas.</strong>{" "}
            {top.length
              ? `Comece pelas próximas ${top.length}.`
              : open.length
                ? "Confira os retornos agendados e os cadastros pendentes."
                : "Esta carteira está sem oportunidades abertas neste retrato."}
          </p>
        </div>
        <button
          className="button secondary"
          onClick={() => setView("pipeline")}
        >
          Ver minha carteira <Icon name="arrow" size={16} />
        </button>
      </div>
      <section className="kpi-grid" aria-label="Resumo da carteira">
        <Kpi
          icon="target"
          label="Prioridades para trabalhar"
          value={top.length}
          note="Urgências e próximos avanços"
        />
        <Kpi
          icon="clock"
          label="Retornos hoje ou vencidos"
          value={due.length}
          note={`${due.filter((d) => d.overdue).length} compromissos vencidos`}
          tone="amber"
        />
        <Kpi
          icon="check"
          label="SQLs em andamento"
          value={qualified.length}
          note="Qualificação confirmada por você"
        />
        <Kpi
          icon="phone"
          label="Contatos registrados hoje"
          value={contactsToday}
          note="Atividade realizada, não envio automático"
        />
      </section>
      <div className="work-layout">
        <FocusQueue top={top} progress={progress} onOpenDeal={setSelected} />
        <aside className="right-column">
          <section className="panel agenda">
            <SectionTitle
              title="Próximos compromissos"
              right={<Icon name="calendar" />}
            />
            <p className="panel-sub">Nenhum próximo passo fica solto.</p>
            {agenda.length ? (
              agenda.slice(0, 4).map((d) => (
                <button
                  key={d.opportunity_id}
                  className="agenda-item"
                  onClick={() => setSelected(d.opportunity_id)}
                >
                  <span
                    className={"agenda-marker " + (d.overdue ? "overdue" : "")}
                  />
                  <div>
                    <small className={d.overdue ? "overdue-text" : ""}>
                      {d.overdue ? "Vencido · " : ""}
                      {dateLabel(d.nextTask.dueAt)}
                    </small>
                    <strong>{d.account || "Conta a identificar"}</strong>
                    <p>{d.nextTask.label}</p>
                  </div>
                  <Icon name="arrow" size={14} />
                </button>
              ))
            ) : (
              <div className="agenda-empty">
                <span className="empty-icon">
                  <Icon name="calendar" size={25} />
                </span>
                <strong>Sua próxima ação começa no contato.</strong>
                <p>
                  Ao registrar uma conversa, combine um retorno. Ele aparece
                  aqui automaticamente.
                </p>
              </div>
            )}
          </section>
          <section className="panel mini-funnel">
            <SectionTitle
              title="Sua carteira em movimento"
              right={<Icon name="funnel" />}
            />
            {STAGES.filter((s) => s.id !== "lost").map((s) => {
              const n = mine.filter((d) => d.status === s.id).length;
              return (
                <div className="mini-stage" key={s.id}>
                  <div>
                    <span>{s.label}</span>
                    <strong>{n}</strong>
                  </div>
                  <div className="mini-track">
                    <span
                      style={{
                        width: `${mine.length ? (n / mine.length) * 100 : 0}%`,
                      }}
                    />
                  </div>
                </div>
              );
            })}
            <button className="text-button" onClick={() => setView("pipeline")}>
              Abrir meu pipeline <Icon name="arrow" size={14} />
            </button>
          </section>
          <div className="data-note">
            <Icon name="info" size={16} />
            <p>
              O dataset não tem telefone ou e-mail. Cadastre um contato
              verificado para habilitar os atalhos de ligação e e-mail.
            </p>
          </div>
        </aside>
      </div>
      {open.some((d) => !d.account) && (
        <button
          className="hygiene-banner"
          onClick={() => {
            setQueue("missing");
            setView("pipeline");
          }}
        >
          <span className="hygiene-icon">
            <Icon name="users" />
          </span>
          <span>
            <strong>
              {open.filter((d) => !d.account).length} oportunidades precisam de
              uma conta identificada.
            </strong>
            <small>
              Uma fila separada para completar contexto, sem tirar o foco das
              negociações.
            </small>
          </span>
          <span>
            Revisar cadastro <Icon name="arrow" size={16} />
          </span>
        </button>
      )}
    </>
  );
}
