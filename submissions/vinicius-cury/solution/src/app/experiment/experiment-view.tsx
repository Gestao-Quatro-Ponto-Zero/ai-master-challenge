"use client";

import { useEffect, useState, useCallback } from "react";

// D2 → D1 mapping for dropdown options
const D2_TO_D1: Record<string, string[]> = {
  Hardware: ["Hardware issue", "Display issue", "Battery life", "Peripheral compatibility"],
  Access: ["Account access", "Network problem", "Software bug"],
  Purchase: ["Payment issue", "Refund request"],
  Storage: ["Data loss"],
  "Internal Project": ["Installation support", "Product setup"],
  "Administrative rights": ["Cancellation request"],
  Miscellaneous: ["Product recommendation", "Product compatibility", "Delivery problem"],
  "HR Support": [],
};

interface ExperimentResult {
  id: number;
  ticket_id: number;
  d2_category: string;
  ticket_text: string;
  zeroshot_d1_subject: string;
  zeroshot_confidence: number;
  zeroshot_reasoning: string;
  zeroshot_model: string;
  human_evaluation: string | null;
  human_correct_subject: string | null;
  human_notes: string | null;
  evaluated_at: string | null;
}

interface LocalEvaluation {
  evaluation: string;
  correctSubject: string;
  notes: string;
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color =
    pct >= 80 ? "bg-green-100 text-green-800" :
    pct >= 50 ? "bg-yellow-100 text-yellow-800" :
    "bg-red-100 text-red-800";
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${color}`}>
      {pct}%
    </span>
  );
}

function TicketCard({
  result,
  localEval,
  onChange,
}: {
  result: ExperimentResult;
  localEval: LocalEvaluation | undefined;
  onChange: (id: number, eval_: LocalEvaluation) => void;
}) {
  const evaluation = localEval?.evaluation || result.human_evaluation || "";
  const correctSubject = localEval?.correctSubject || result.human_correct_subject || "";
  const notes = localEval?.notes || result.human_notes || "";
  const d1Options = D2_TO_D1[result.d2_category] || [];
  const isSaved = !localEval && !!result.human_evaluation;

  const update = (partial: Partial<LocalEvaluation>) => {
    onChange(result.id, {
      evaluation: partial.evaluation ?? evaluation,
      correctSubject: partial.correctSubject ?? correctSubject,
      notes: partial.notes ?? notes,
    });
  };

  return (
    <div className={`rounded-lg border p-4 space-y-3 ${isSaved ? "border-green-200 bg-green-50/30" : "border-border"}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
            {result.d2_category}
          </span>
          <span className="text-xs text-muted-foreground">#{result.ticket_id}</span>
        </div>
        {isSaved && (
          <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
            Salvo
          </span>
        )}
      </div>

      {/* Ticket text */}
      <div className="rounded bg-muted/50 p-3">
        <p className="text-sm leading-relaxed">{result.ticket_text}</p>
      </div>

      {/* Zero-shot result */}
      <div className="rounded border border-dashed p-3 space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">
            Zero-shot: <span className="text-blue-600">{result.zeroshot_d1_subject}</span>
          </span>
          <ConfidenceBadge confidence={result.zeroshot_confidence} />
        </div>
        <p className="text-xs text-muted-foreground">{result.zeroshot_reasoning}</p>
      </div>

      {/* D1 options reference */}
      <div className="rounded bg-blue-50/50 border border-blue-100 p-2">
        <span className="text-xs font-medium text-blue-700">Opções D1 para {result.d2_category}: </span>
        <span className="text-xs text-blue-600">
          {d1Options.length > 0
            ? d1Options.map((opt, i) => (
                <span key={opt}>
                  {result.zeroshot_d1_subject === opt ? <strong>{opt}</strong> : opt}
                  {i < d1Options.length - 1 ? " · " : ""}
                </span>
              ))
            : "nenhuma (Other esperado)"
          }
          {d1Options.length > 0 && <span> · <em>Other</em></span>}
        </span>
      </div>

      {/* Evaluation buttons */}
      <div className="flex items-center gap-2 border-t pt-3">
        {(["correct", "wrong"] as const).map((val) => {
          const labels = { correct: "Correto", wrong: "Errado" };
          const colors = {
            correct: evaluation === val ? "bg-green-600 text-white" : "bg-green-100 text-green-800 hover:bg-green-200",
            wrong: evaluation === val ? "bg-red-600 text-white" : "bg-red-100 text-red-800 hover:bg-red-200",
          };
          return (
            <button
              key={val}
              onClick={() => update({ evaluation: val })}
              className={`rounded px-4 py-1.5 text-xs font-medium transition-colors ${colors[val]}`}
            >
              {labels[val]}
            </button>
          );
        })}

        {/* When wrong: show correct subject selector inline */}
        {evaluation === "wrong" && (
          <select
            value={correctSubject}
            onChange={(e) => update({ correctSubject: e.target.value })}
            className="rounded border px-2 py-1 text-xs flex-1 ml-2"
          >
            <option value="">Qual seria o correto?</option>
            {d1Options.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
            <option value="Other">Other</option>
          </select>
        )}
      </div>
    </div>
  );
}

export function ExperimentView() {
  const [results, setResults] = useState<ExperimentResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [localEvals, setLocalEvals] = useState<Record<number, LocalEvaluation>>({});
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");

  useEffect(() => {
    fetch("/api/experiment")
      .then((r) => r.json())
      .then((data) => {
        setResults(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleChange = useCallback((id: number, eval_: LocalEvaluation) => {
    setLocalEvals((prev) => ({ ...prev, [id]: eval_ }));
    setSaveMessage("");
  }, []);

  const handleSaveAll = async () => {
    const entries = Object.entries(localEvals);
    if (entries.length === 0) return;

    setSaving(true);
    setSaveMessage("");
    let saved = 0;

    for (const [idStr, eval_] of entries) {
      const id = Number(idStr);
      if (!eval_.evaluation) continue;

      const resp = await fetch("/api/experiment", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id,
          human_evaluation: eval_.evaluation,
          human_correct_subject: eval_.correctSubject || null,
          human_notes: eval_.notes || null,
        }),
      });

      if (resp.ok) {
        const updated = await resp.json();
        setResults((prev) =>
          prev.map((r) => (r.id === id ? { ...r, ...updated } : r))
        );
        saved++;
      }
    }

    setLocalEvals({});
    setSaving(false);
    setSaveMessage(`${saved} avaliações salvas!`);
    setTimeout(() => setSaveMessage(""), 3000);
  };

  const categories = [...new Set(results.map((r) => r.d2_category))];
  const filtered = results.filter((r) => {
    if (filter !== "all" && r.d2_category !== filter) return false;
    if (statusFilter === "pending" && r.human_evaluation) return false;
    if (statusFilter === "evaluated" && !r.human_evaluation) return false;
    return true;
  });

  // Count from saved results + local unsaved evaluations
  const allEvals = results.map((r) => {
    const local = localEvals[r.id];
    return local?.evaluation || r.human_evaluation || null;
  });
  const totalEvaluated = allEvals.filter(Boolean).length;
  const totalCorrect = allEvals.filter((e) => e === "correct").length;
  const totalWrong = allEvals.filter((e) => e === "wrong").length;
  const unsavedCount = Object.values(localEvals).filter((e) => e.evaluation).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <p className="text-muted-foreground">Carregando experimento...</p>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 gap-4">
        <p className="text-muted-foreground text-lg">Nenhum resultado encontrado.</p>
        <p className="text-sm text-muted-foreground">
          Execute o script: <code className="bg-muted px-2 py-0.5 rounded">python scripts/run_experiment.py</code>
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Stats bar */}
      <div className="grid grid-cols-4 gap-4">
        <div className="rounded-lg border p-3 text-center">
          <div className="text-2xl font-bold">{results.length}</div>
          <div className="text-xs text-muted-foreground">Total</div>
        </div>
        <div className="rounded-lg border p-3 text-center">
          <div className="text-2xl font-bold">{totalEvaluated}</div>
          <div className="text-xs text-muted-foreground">Avaliados</div>
        </div>
        <div className="rounded-lg border border-green-200 bg-green-50/50 p-3 text-center">
          <div className="text-2xl font-bold text-green-700">{totalCorrect}</div>
          <div className="text-xs text-green-600">Corretos</div>
        </div>
        <div className="rounded-lg border border-red-200 bg-red-50/50 p-3 text-center">
          <div className="text-2xl font-bold text-red-700">{totalWrong}</div>
          <div className="text-xs text-red-600">Errados</div>
        </div>
      </div>

      {/* Accuracy (when evaluated) */}
      {totalEvaluated > 0 && (
        <div className="rounded-lg border bg-muted/30 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">
              Acurácia zero-shot (subcategorização):
            </span>
            <span className="text-lg font-bold">
              {Math.round((totalCorrect / totalEvaluated) * 100)}%
              <span className="text-sm font-normal text-muted-foreground ml-1">
                ({totalCorrect}/{totalEvaluated})
              </span>
            </span>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Categoria:</span>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="rounded border px-2 py-1 text-sm"
          >
            <option value="all">Todas ({results.length})</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat} ({results.filter((r) => r.d2_category === cat).length})
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded border px-2 py-1 text-sm"
          >
            <option value="all">Todos</option>
            <option value="pending">Pendentes</option>
            <option value="evaluated">Avaliados</option>
          </select>
        </div>
        <span className="text-xs text-muted-foreground ml-auto">
          Mostrando {filtered.length} de {results.length}
        </span>
      </div>

      {/* Cards grouped by category */}
      {categories
        .filter((cat) => filter === "all" || cat === filter)
        .map((cat) => {
          const catResults = filtered.filter((r) => r.d2_category === cat);
          if (catResults.length === 0) return null;

          return (
            <div key={cat} className="space-y-3">
              <h2 className="text-lg font-semibold">{cat}</h2>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {catResults.map((result) => (
                  <TicketCard
                    key={result.id}
                    result={result}
                    localEval={localEvals[result.id]}
                    onChange={handleChange}
                  />
                ))}
              </div>
            </div>
          );
        })}

      {/* Sticky save bar */}
      <div className="sticky bottom-0 bg-background border-t p-4 -mx-6 -mb-6 flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {unsavedCount > 0
            ? `${unsavedCount} avaliação(ões) não salva(s)`
            : "Todas as avaliações salvas"
          }
          {saveMessage && (
            <span className="ml-3 text-green-600 font-medium">{saveMessage}</span>
          )}
        </div>
        <button
          onClick={handleSaveAll}
          disabled={unsavedCount === 0 || saving}
          className={`rounded px-6 py-2 text-sm font-medium transition-colors ${
            unsavedCount === 0 || saving
              ? "bg-muted text-muted-foreground cursor-not-allowed"
              : "bg-primary text-primary-foreground hover:bg-primary/90"
          }`}
        >
          {saving ? "Salvando..." : `Salvar Tudo (${unsavedCount})`}
        </button>
      </div>
    </div>
  );
}
