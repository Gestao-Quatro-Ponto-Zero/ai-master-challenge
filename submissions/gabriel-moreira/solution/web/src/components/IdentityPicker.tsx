import { useState } from "react";
import { api, ApiError } from "../api";
import { useAsync } from "../hooks/useAsync";
import type { Session } from "../types";

interface Props {
  onIdentified: (session: Session) => void;
}

export function IdentityPicker({ onIdentified }: Props) {
  const { data: identities, loading, error } = useAsync(() => api.getIdentities(), []);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function handleSelect(name: string) {
    setSubmitting(true);
    setSubmitError(null);
    try {
      const session = await api.identify(name);
      onIdentified(session);
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : "falha ao identificar");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg px-4">
      <div className="w-full max-w-2xl bg-white border border-border rounded-lg p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-navy mb-1">Pipeline Priorizado</h1>
        <p className="text-muted mb-6">Quem é você? Selecione sua identidade para ver seu pipeline.</p>

        {loading && <p className="text-muted">Carregando identidades…</p>}
        {error && <p className="text-alert">Não foi possível carregar as identidades: {error}</p>}
        {submitError && <p className="text-alert mb-4">{submitError}</p>}

        {identities && (
          <div className="grid gap-6 sm:grid-cols-3">
            <IdentityGroup
              title="Vendedor"
              names={identities.sales_agents}
              disabled={submitting}
              onSelect={handleSelect}
            />
            <IdentityGroup
              title="Supervisor"
              names={identities.supervisors}
              disabled={submitting}
              onSelect={handleSelect}
            />
            <IdentityGroup
              title="Escritório (Manager)"
              names={identities.managers}
              disabled={submitting}
              onSelect={handleSelect}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function IdentityGroup({
  title,
  names,
  disabled,
  onSelect,
}: {
  title: string;
  names: string[];
  disabled: boolean;
  onSelect: (name: string) => void;
}) {
  return (
    <div>
      <h2 className="text-sm font-semibold text-navy mb-2">{title}</h2>
      <div className="flex flex-col gap-1 max-h-72 overflow-y-auto pr-1">
        {names.map((name) => (
          <button
            key={name}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(name)}
            className="text-left text-sm px-3 py-2 rounded-xs border border-border hover:border-gold hover:bg-gold/5 transition-colors disabled:opacity-50"
          >
            {name}
          </button>
        ))}
      </div>
    </div>
  );
}
