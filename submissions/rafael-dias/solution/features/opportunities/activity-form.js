"use client";

import EvidenceFields from "./evidence-fields";
import Icon from "../../components/ui/icon";
import { actionGuide } from "../../lib/sales-guide.mjs";
export default function ActivityForm({
  deal: d,
  action,
  onActionChange,
  formError,
  disabled,
  onSubmit,
}) {
  return (
    <form onSubmit={onSubmit} className="activity-form">
      <label>
        O que aconteceu?
        <select value={action} onChange={(e) => onActionChange(e.target.value)}>
          <option value="profile">Identifiquei ou atualizei o contato</option>
          <option value="contact">
            Conversei com o cliente ou tentei contato
          </option>
          <option value="qualify">
            Confirmei necessidade, decisor e prazo (SQL)
          </option>
          <option value="proposal">Enviei a proposta ao cliente</option>
          <option value="followup">Combinei um retorno</option>
          <option value="won">Cliente confirmou a compra</option>
          <option value="lost">A oportunidade foi perdida</option>
          <option value="pause">Cliente pediu uma pausa</option>
          <option value="note">Quero registrar uma observação</option>
        </select>
      </label>
      <div key={action}>
        {action === "profile" ? (
          <>
            <p className="form-hint">
              Use informações verificadas. O cadastro fica somente neste
              navegador.
            </p>
            <label>
              Empresa / conta
              <input
                name="account"
                required
                readOnly={!!d.originalAccount}
                defaultValue={d.account || ""}
                placeholder="Nome da empresa"
                maxLength={180}
              />
            </label>
            <label>
              Nome do contato
              <input
                name="contactName"
                required
                defaultValue={d.contact?.name || ""}
                placeholder="Quem participa da decisão?"
                maxLength={180}
              />
            </label>
            <div className="form-grid">
              <label>
                E-mail
                <input
                  name="email"
                  type="email"
                  defaultValue={d.contact?.email || ""}
                  placeholder="contato@empresa.com"
                  maxLength={180}
                />
              </label>
              <label>
                Telefone
                <input
                  name="phone"
                  type="tel"
                  defaultValue={d.contact?.phone || ""}
                  placeholder="+55 ..."
                  maxLength={40}
                />
              </label>
            </div>
          </>
        ) : (
          <>
            <label>
              {action === "lost"
                ? "Qual foi o motivo da perda?"
                : action === "won"
                  ? "Como a venda foi confirmada?"
                  : "Resultado / contexto da ação"}
              <textarea
                name="notes"
                required
                maxLength={2000}
                placeholder={
                  action === "contact"
                    ? "Houve resposta? O que foi combinado? Se não houve, registre a tentativa."
                    : "Registre o que foi confirmado, sem suposições."
                }
                rows={3}
              />
            </label>
            <EvidenceFields action={action} />
            {action === "qualify" && (
              <div className="qualify-fields">
                <p className="form-hint">
                  Score alto não confirma SQL. Registre as três evidências
                  comerciais.
                </p>
                <label>
                  Necessidade validada
                  <input
                    name="need"
                    required
                    placeholder="Qual problema o cliente quer resolver?"
                    maxLength={500}
                  />
                </label>
                <label>
                  Decisor / processo de decisão
                  <input
                    name="authority"
                    required
                    placeholder="Quem decide e como?"
                    maxLength={500}
                  />
                </label>
                <label>
                  Prazo de compra
                  <input
                    name="timing"
                    required
                    placeholder="Quando pretende decidir?"
                    maxLength={500}
                  />
                </label>
              </div>
            )}
            {action === "won" && (
              <label>
                Valor real da venda (USD)
                <input
                  name="amount"
                  type="number"
                  required
                  min="0.01"
                  step="0.01"
                  placeholder="0,00"
                />
              </label>
            )}
            {["contact", "qualify", "proposal", "followup"].includes(
              action,
            ) && (
              <div className="next-step-fields">
                <div className="eyebrow">E DEPOIS DISSO?</div>
                <label>
                  Cliente aceitou esse próximo passo?
                  <select name="nextStepAccepted" defaultValue="unknown">
                    <option value="unknown">Não informado</option>
                    <option value="yes">Sim, confirmou</option>
                    <option value="no">Não, é um agendamento interno</option>
                  </select>
                </label>
                <label>
                  Próximo passo combinado
                  <input
                    name="nextAction"
                    required
                    defaultValue={actionGuide(d, action).suggestedNext || ""}
                    placeholder={
                      action === "proposal"
                        ? "Retomar proposta e critérios de decisão"
                        : "Ex.: apresentar solução ao decisor"
                    }
                    maxLength={300}
                  />
                </label>
                <label>
                  Data e hora do próximo passo
                  <input name="dueAt" type="datetime-local" required />
                </label>
                <small>
                  O próximo compromisso substitui o anterior e alimenta sua
                  agenda.
                </small>
              </div>
            )}
          </>
        )}
      </div>
      {formError && (
        <p className="form-error" role="alert">
          {formError}
        </p>
      )}
      <button
        className="button primary form-submit"
        disabled={disabled}
        type="submit"
      >
        <Icon name="check" size={17} />
        {action === "qualify"
          ? "Confirmar SQL e próximo passo"
          : action === "won"
            ? "Registrar venda"
            : action === "pause"
              ? "Salvar pausa solicitada"
              : action === "profile"
                ? "Salvar contato"
                : action === "lost"
                  ? "Registrar perda"
                  : action === "note"
                    ? "Salvar anotação"
                    : "Salvar resultado e próximo passo"}
      </button>
      <p className="form-footnote">
        Registro manual da demonstração. Não envia mensagens nem altera o CRM
        original.
      </p>
    </form>
  );
}
