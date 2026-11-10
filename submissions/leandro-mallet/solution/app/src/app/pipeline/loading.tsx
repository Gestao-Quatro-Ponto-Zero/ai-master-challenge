import { Esqueleto } from "@/components/Estado";

export default function Carregando() {
  return (
    <div className="grid gap-4" aria-busy="true" aria-label="Carregando o pipeline">
      <Esqueleto className="h-8 w-40" />
      <Esqueleto className="h-10 w-full" />
      <div className="grid gap-4 md:grid-cols-2">
        {[0, 1].map((c) => (
          <div key={c} className="grid gap-2 rounded-cartao border border-linha bg-marfim p-3">
            <Esqueleto className="h-6 w-1/2" />
            {[0, 1, 2, 3].map((i) => (
              <Esqueleto key={i} className="h-32" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
