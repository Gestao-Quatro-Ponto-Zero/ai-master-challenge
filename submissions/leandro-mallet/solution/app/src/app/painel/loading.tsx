import { Esqueleto } from "@/components/Estado";

export default function Carregando() {
  return (
    <div className="grid gap-5" aria-busy="true" aria-label="Carregando o painel">
      <Esqueleto className="h-8 w-40" />
      <div className="grid gap-5 lg:grid-cols-[1fr_22rem]">
        <div className="order-2 grid content-start gap-5 lg:order-1">
          <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
            {Array.from({ length: 8 }, (_, i) => (
              <Esqueleto key={i} className="h-28" />
            ))}
          </div>
          <Esqueleto className="h-56" />
        </div>
        <div className="order-1 grid content-start gap-2 lg:order-2">
          {Array.from({ length: 5 }, (_, i) => (
            <Esqueleto key={i} className="h-24" />
          ))}
        </div>
      </div>
    </div>
  );
}
