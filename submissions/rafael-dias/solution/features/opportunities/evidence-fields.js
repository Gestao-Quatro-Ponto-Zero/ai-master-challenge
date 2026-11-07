"use client";

function localTimestamp() {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
}

/** Small, contextual inputs. Unknown is explicit; it never means rejection. */
export default function EvidenceFields({ action }) {
  if (!["contact", "qualify", "proposal", "followup", "pause"].includes(action))
    return null;
  return (
    <section className="evidence-fields" aria-label="Evidências da conversa">
      <div className="eyebrow">O QUE O CLIENTE CONFIRMOU</div>
      <p>
        Declare apenas o que aconteceu. Sem informação, deixe “Não informado”.
      </p>
      <div className="form-grid">
        <label>
          Houve resposta do cliente?
          <select name="buyerResponse" defaultValue="unknown">
            <option value="unknown">Não informado</option>
            <option value="confirmed">Sim, houve conversa ou resposta</option>
            <option value="none">Não, foi uma tentativa sem resposta</option>
          </select>
        </label>
        <label>
          Quando essa ação aconteceu?
          <input
            name="occurredAt"
            type="datetime-local"
            defaultValue={localTimestamp()}
            required
          />
        </label>
      </div>
      {action === "proposal" && (
        <>
          <div className="form-grid">
            <label>
              Valor da proposta (USD) · opcional
              <input
                name="quotedAmount"
                type="number"
                min="0.01"
                step="0.01"
                placeholder="Valor total informado, sem estimar"
              />
            </label>
            <label>
              Condições financeiras
              <select name="financialStatus" defaultValue="unknown">
                <option value="unknown">A confirmar</option>
                <option value="compatible">
                  Cliente confirmou compatibilidade
                </option>
                <option value="blocked">Cliente informou um bloqueio</option>
              </select>
            </label>
          </div>
          <input name="quoteCurrency" type="hidden" value="USD" />
        </>
      )}
      {action === "pause" && (
        <label>
          Retomar após a pausa em
          <input name="pauseUntil" type="datetime-local" required />
        </label>
      )}
    </section>
  );
}
