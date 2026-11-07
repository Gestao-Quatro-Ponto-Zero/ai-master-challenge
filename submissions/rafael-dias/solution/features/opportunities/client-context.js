import Icon from "../../components/ui/icon";
import { Score } from "../../components/ui/primitives";
import { fmt, usd, stageName } from "../../lib/format.mjs";
import { reasonFor } from "../../lib/workflow.mjs";
import HealthSummary from "./health-summary";
export default function ClientContext({ deal: d }) {
  return (
    <div className="client-context">
      <div className="score-panel">
        <Score deal={d} large />
        <div>
          <strong>Referência histórica</strong>
          <span>{stageName(d.status)}</span>
          <small>Não é probabilidade de venda.</small>
        </div>
      </div>
      <HealthSummary deal={d} />
      <section className="client-details">
        <h3>Cliente e motivo da prioridade</h3>
        <h3>Por que esta prioridade?</h3>
        <p className="reason-copy">{reasonFor(d)}</p>
        <div className="score-factors">
          {d.factors.map((f) => (
            <div className="score-factor" key={f.label}>
              <div>
                <span>{f.label}</span>
                <strong>+{f.points}</strong>
              </div>
              <progress max={f.max} value={f.points} />
            </div>
          ))}
        </div>
        <div className="client-info">
          <h3>O que sabemos sobre a empresa</h3>
          <p className="context-source">
            Informações do CRM fornecido · referência 2017
          </p>
          <dl>
            <dt>Setor</dt>
            <dd>{d.sector || "Não informado"}</dd>
            <dt>Localização</dt>
            <dd>{d.location || "Não informada"}</dd>
            <dt>Funcionários</dt>
            <dd>
              {d.employees === null ? "Não informado" : fmt.format(d.employees)}
            </dd>
            <dt>Receita anual</dt>
            <dd>
              {d.revenue === null
                ? "Não informada"
                : `${fmt.format(d.revenue)} milhões USD`}
            </dd>
            <dt>Preço de catálogo</dt>
            <dd>{usd.format(d.sales_price)} / unidade</dd>
            {d.quote && (
              <>
                <dt>Proposta informada</dt>
                <dd>{usd.format(d.quote.amount)} · total em USD</dd>
              </>
            )}
            <dt>Ano de fundação</dt>
            <dd>{d.year_established || "Não informado"}</dd>
            <dt>Tempo na base original</dt>
            <dd>
              {d.age === null
                ? "Não disponível"
                : `${d.age} dias · típico ${d.reference.days}`}
            </dd>
          </dl>
        </div>
        {d.account_history && (
          <section className="account-track">
            <h3>Relacionamento na base histórica</h3>
            <div>
              <strong>{d.account_history.won}</strong>
              <span>negócios ganhos com esta conta</span>
            </div>
            {d.account_history.lastWonDate ? (
              <p>
                Último ganho registrado:{" "}
                {new Date(
                  d.account_history.lastWonDate + "T12:00:00",
                ).toLocaleDateString("pt-BR")}{" "}
                · {d.account_history.lastWonProduct}.
              </p>
            ) : (
              <p>Não há venda ganha registrada para esta conta.</p>
            )}
            <small>
              Histórico até 31/12/2017. Não confirma intenção atual e não altera
              o score.
            </small>
          </section>
        )}
        {!d.qualification && (
          <section className="missing-context">
            <h3>O que falta descobrir na conversa</h3>
            <ul>
              <li>Qual problema o cliente precisa resolver?</li>
              <li>Quem decide a compra?</li>
              <li>Quando pretende avançar?</li>
            </ul>
          </section>
        )}
        <div className="contact-info">
          <h3>Contato</h3>
          {d.contact ? (
            <>
              <strong>{d.contact.name}</strong>
              {d.contact.email && (
                <a href={`mailto:${d.contact.email}`}>
                  <Icon name="mail" size={14} />
                  {d.contact.email}
                </a>
              )}
              {d.contact.phone && (
                <a href={`tel:${d.contact.phone.replace(/[^+\d]/g, "")}`}>
                  <Icon name="phone" size={14} />
                  {d.contact.phone}
                </a>
              )}
              <small>Informado nesta demonstração.</small>
            </>
          ) : (
            <p>
              Nome, telefone e e-mail não constam na base. Adicione dados
              verificados para habilitar os atalhos.
            </p>
          )}
        </div>
        {d.qualification && (
          <div className="qualification-box">
            <span className="tiny-label">EVIDÊNCIAS DO SQL</span>
            <p>
              <strong>Necessidade:</strong> {d.qualification.need}
            </p>
            <p>
              <strong>Decisor:</strong> {d.qualification.authority}
            </p>
            <p>
              <strong>Prazo:</strong> {d.qualification.timing}
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
