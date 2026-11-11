import { Esqueleto } from "@/components/Estado";

export default function Carregando() {
  return (
    <div className="grid gap-4" aria-busy="true" aria-label="Carregando os leads">
      <Esqueleto className="h-8 w-40" />
      <Esqueleto className="h-10 w-full" />
      <div className="grid gap-2 rounded-cartao border border-borda p-3">
        {Array.from({ length: 8 }, (_, i) => (
          <Esqueleto key={i} className="h-10" />
        ))}
      </div>
    </div>
  );
}
