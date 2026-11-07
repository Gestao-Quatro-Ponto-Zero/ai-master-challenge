"use client";

import { useEffect, useRef, useState } from "react";
import Icon from "../../components/ui/icon";
import { Empty } from "../../components/ui/primitives";
import { usd, dateLabel } from "../../lib/format.mjs";
import { eventNames } from "../../lib/activity.mjs";
import { isClosed } from "../../lib/workflow.mjs";
import {
  actionGuide,
  afterAction,
  recommendedAction,
} from "../../lib/sales-guide.mjs";
import SpinGuide from "./spin-guide";
import ActivityForm from "./activity-form";
import ClientContext from "./client-context";
export default function OpportunityDialog({
  deal: d,
  onClose,
  onRecord,
  disabled,
  initialAction,
}) {
  const ref = useRef(null),
    [tab, setTab] = useState("action"),
    [action, setAction] = useState(initialAction || recommendedAction(d)),
    [formError, setFormError] = useState(""),
    [saved, setSaved] = useState(""),
    [savedType, setSavedType] = useState(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog.showModal();
    if (initialAction) dialog.querySelector("textarea,input")?.focus();
    return () => {
      if (dialog.open) dialog.close();
    };
  }, []);
  useEffect(() => {
    ref.current
      ?.querySelector(".dialog-body")
      ?.scrollTo({ top: 0, behavior: "auto" });
  }, [tab]);
  function submit(e) {
    e.preventDefault();
    const values = Object.fromEntries(new FormData(e.currentTarget));
    values.type = action;
    const error = onRecord(values);
    if (error) {
      setFormError(error);
      return;
    }
    if (initialAction) {
      onClose();
      return;
    }
    setFormError("");
    setSaved(eventNames[action]);
    setSavedType(action);
    setTab("timeline");
  }
  const actionable = !isClosed(d);
  const [guideAction, setGuideAction] = useState(
    initialAction || recommendedAction(d),
  );
  const guide = actionGuide(d, guideAction);
  const after = savedType ? afterAction(savedType, d) : null;
  function chooseAction(type) {
    setAction(type);
    setGuideAction(type);
    setFormError("");
    setTab("action");
  }
  return (
    <dialog
      ref={ref}
      className={`deal-dialog ${initialAction ? "record-only" : ""}`}
      onCancel={onClose}
      onClick={(e) => {
        if (e.target === ref.current) onClose();
      }}
    >
      <div className="dialog-header">
        <div>
          <span className="eyebrow">
            {initialAction ? "REGISTRAR AVANÇO" : "OPORTUNIDADE"} ·{" "}
            {d.opportunity_id}
          </span>
          <h2>{d.account || "Conta a identificar"}</h2>
          <p>
            {d.product} <span>·</span> {d.sales_agent}
          </p>
        </div>
        <button
          className="icon-button"
          onClick={onClose}
          aria-label="Fechar oportunidade"
        >
          <Icon name="close" />
        </button>
      </div>
      <div className={`dialog-body action-${action}`}>
        {!initialAction && <ClientContext deal={d} />}
        <div className="deal-work">
          {!initialAction && (
            <div className="dialog-tabs">
              <button
                className={tab === "action" ? "active" : ""}
                onClick={() => setTab("action")}
              >
                Próxima ação
              </button>
              <button
                className={tab === "timeline" ? "active" : ""}
                onClick={() => setTab("timeline")}
              >
                Histórico <span>{d.activities.length}</span>
              </button>
              <button
                className="register-shortcut"
                onClick={() => {
                  setTab("action");
                  requestAnimationFrame(() =>
                    ref.current
                      ?.querySelector("#register-result")
                      ?.scrollIntoView({
                        behavior: "smooth",
                        block: "start",
                      }),
                  );
                }}
              >
                Registrar resultado ↗
              </button>
            </div>
          )}
          {tab === "action" ? (
            <>
              {!initialAction && (
                <>
                  <div className="playbook">
                    <span className="eyebrow">O QUE FAZER AGORA</span>
                    <h3>{guide.title}</h3>
                    <p className="guide-objective">{guide.objective}</p>
                    <ol>
                      {guide.steps.map((s) => (
                        <li key={s}>{s}</li>
                      ))}
                    </ol>
                  </div>
                  {actionable &&
                    ["contact", "qualify", "profile"].includes(guideAction) && (
                      <SpinGuide deal={d} />
                    )}
                </>
              )}
              {d.nextTask && (
                <div className={"commitment " + (d.overdue ? "late" : "")}>
                  <Icon name="clock" size={17} />
                  <div>
                    <small>
                      PRÓXIMO COMPROMISSO {d.overdue ? "· VENCIDO" : ""}
                    </small>
                    <strong>{d.nextTask.label}</strong>
                    <span>{dateLabel(d.nextTask.dueAt)}</span>
                  </div>
                </div>
              )}
              {actionable ? (
                <section className="quick-record" id="register-result">
                  <h3 className="record-heading">
                    Registrar resultado e próximo passo
                  </h3>
                  <p className="result-instruction">
                    Selecione o que aconteceu e complete os campos abaixo. A
                    oportunidade só muda depois de salvar.
                  </p>
                  {initialAction && (
                    <p className="record-intro">
                      Confirme o que aconteceu. A oportunidade só muda de etapa
                      depois de salvar.
                    </p>
                  )}
                  <ActivityForm
                    deal={d}
                    action={action}
                    onActionChange={(value) => {
                      setAction(value);
                      setFormError("");
                    }}
                    formError={formError}
                    disabled={disabled}
                    onSubmit={submit}
                  />
                </section>
              ) : (
                <div className="closed-state">
                  <Icon
                    name={d.status === "won" ? "trophy" : "check"}
                    size={30}
                  />
                  <h3>
                    {d.status === "won"
                      ? "Venda registrada!"
                      : "Perda registrada"}
                  </h3>
                  <p>
                    {d.status === "won"
                      ? usd.format(d.actualValue)
                      : "O motivo ficou salvo no histórico."}
                  </p>
                </div>
              )}
            </>
          ) : (
            <div className="timeline">
              {saved && (
                <div className="inline-success" role="status">
                  <Icon name="check" size={17} />
                  {saved}. Registro salvo.
                </div>
              )}
              {after && (
                <section className="after-action">
                  <span className="eyebrow">PRÓXIMO PASSO</span>
                  <h3>{after.title}</h3>
                  <p>{after.text}</p>
                  {d.nextTask && (
                    <small>
                      Retorno combinado: {dateLabel(d.nextTask.dueAt)} ·{" "}
                      {d.nextTask.label}
                    </small>
                  )}
                  {actionable && after.action && (
                    <button
                      type="button"
                      className="button secondary"
                      onClick={() => chooseAction(after.action)}
                    >
                      Preparar próximo passo <Icon name="arrow" size={15} />
                    </button>
                  )}
                </section>
              )}
              {!d.activities.length ? (
                <Empty
                  title="Vamos escrever o próximo capítulo?"
                  text="Registre um contato para começar o histórico desta oportunidade."
                />
              ) : (
                [...d.activities].reverse().map((e) => (
                  <article className="timeline-item" key={e.id}>
                    <span className="timeline-dot" />
                    <small>
                      {dateLabel(e.occurredAt || e.at)} · {e.agent}
                    </small>
                    <h3>{eventNames[e.type]}</h3>
                    <p>{e.notes || `${e.contactName} · ${e.account}`}</p>
                    {e.buyerResponse && (
                      <p>
                        Resposta do cliente:{" "}
                        {e.buyerResponse === "confirmed"
                          ? "conversa confirmada"
                          : e.buyerResponse === "none"
                            ? "tentativa sem resposta"
                            : "não informada"}
                        . Declaração do vendedor.
                      </p>
                    )}
                    {e.nextStepAccepted && (
                      <p>
                        Aceite do próximo passo:{" "}
                        {e.nextStepAccepted === "yes"
                          ? "confirmado"
                          : e.nextStepAccepted === "no"
                            ? "agendamento interno"
                            : "não informado"}
                        .
                      </p>
                    )}
                    {e.quotedAmount && (
                      <p>
                        Proposta informada: {usd.format(Number(e.quotedAmount))}
                        .
                      </p>
                    )}
                    {e.pauseUntil && (
                      <p>Pausa até {dateLabel(e.pauseUntil)}.</p>
                    )}
                    {e.type === "profile" && <p>{e.email || e.phone}</p>}
                    {e.need && (
                      <p>
                        Necessidade: {e.need}
                        <br />
                        Decisor: {e.authority}
                        <br />
                        Prazo: {e.timing}
                      </p>
                    )}
                    {e.nextAction && (
                      <div className="timeline-next">
                        <strong>Próximo passo: {e.nextAction}</strong>
                        <span>{dateLabel(e.dueAt)}</span>
                      </div>
                    )}
                    {e.type === "won" && (
                      <strong>{usd.format(Number(e.amount))}</strong>
                    )}
                  </article>
                ))
              )}
              {actionable && (
                <button
                  className="button secondary"
                  onClick={() => {
                    setSaved("");
                    setTab("action");
                  }}
                >
                  Registrar próxima ação <Icon name="arrow" size={15} />
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </dialog>
  );
}
