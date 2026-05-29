import type { RagSource } from "@/lib/types";

type RagSuggestionProps = {
  suggestion: string;
  confidence: number;
  sources: RagSource[];
};

export function RagSuggestion({ suggestion, confidence, sources }: RagSuggestionProps) {
  const confidenceLabel = confidence >= 0.75 ? "Alta" : confidence >= 0.5 ? "Média" : "Baixa";

  return (
    <section className="card p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Sugestão da IA</h3>
        <span className="chip">
          Confiança: {confidenceLabel} ({Math.round(confidence * 100)}%)
        </span>
      </div>

      <p className="mt-3 text-sm leading-6 text-slate-700">{suggestion}</p>

      <div className="mt-4">
        <p className="text-xs uppercase tracking-wide text-slate-500">Tickets similares</p>
        <ul className="mt-2 space-y-2">
          {sources.map((source) => (
            <li key={source.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
              <p className="font-medium text-slate-900">{source.description}</p>
              <p className="mt-1 text-xs text-slate-600">Resolução: {source.resolution}</p>
              <p className="mt-1 text-xs text-[hsl(var(--accent))]">
                Similaridade: {Math.round(source.similarity * 100)}%
              </p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
