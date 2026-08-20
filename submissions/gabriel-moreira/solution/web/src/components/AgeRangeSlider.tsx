import { useEffect, useState } from "react";

const CENSURA_DIAS = 138;

/** Filtro de idade como régua de dois cursores — limites derivados do
 * funil (endpoint de opções de filtro), nunca de `Math.min`/`Math.max`
 * no cliente, que com paginação nunca vê todas as idades de uma vez
 * (Requirement "Régua de idade", design.md decisão 6). Confirma no
 * solto do cursor (mouse/touch/teclado), não a cada pixel arrastado. */
export function AgeRangeSlider({
  bounds,
  value,
  excluidasSemIdade,
  onCommit,
}: {
  bounds: [number, number];
  value: [number, number];
  excluidasSemIdade: number;
  onCommit: (min: number, max: number) => void;
}) {
  const [boundsMin, boundsMax] = bounds;
  const [local, setLocal] = useState<[number, number]>(value);

  useEffect(() => {
    setLocal(value);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value[0], value[1]]);

  const [lo, hi] = local;
  const range = boundsMax - boundsMin || 1;
  const pctLo = ((lo - boundsMin) / range) * 100;
  const pctHi = ((hi - boundsMin) / range) * 100;
  const censuraNoIntervalo = CENSURA_DIAS >= boundsMin && CENSURA_DIAS <= boundsMax;
  const pctCensura = ((CENSURA_DIAS - boundsMin) / range) * 100;
  const emIntervaloCompleto = lo === boundsMin && hi === boundsMax;

  function commit(next: [number, number]) {
    onCommit(next[0], next[1]);
  }

  function handleMinChange(v: number) {
    setLocal(([, curHi]) => [Math.min(v, curHi), curHi]);
  }

  function handleMaxChange(v: number) {
    setLocal(([curLo]) => [curLo, Math.max(v, curLo)]);
  }

  return (
    <div className="flex flex-col gap-2 min-w-[16rem]">
      <div className="flex items-center justify-between text-xs text-muted">
        <span>Idade (dias)</span>
        <span className="font-semibold text-navy">
          {Math.round(lo)}–{Math.round(hi)} dias
        </span>
      </div>

      <div className="relative h-11 flex items-center">
        <div className="absolute left-0 right-0 h-1.5 bg-border rounded-full pointer-events-none" />
        <div
          className="absolute h-1.5 bg-gold rounded-full pointer-events-none"
          style={{ left: `${pctLo}%`, right: `${100 - pctHi}%` }}
        />
        {censuraNoIntervalo && (
          <div
            className="absolute top-0 h-full border-l-2 border-dashed border-alert/60 pointer-events-none"
            style={{ left: `${pctCensura}%` }}
          >
            <span className="absolute -top-4 left-1 text-[10px] text-alert whitespace-nowrap">
              138d sem precedente
            </span>
          </div>
        )}
        <input
          type="range"
          aria-label="Idade mínima em dias"
          min={boundsMin}
          max={boundsMax}
          value={lo}
          onChange={(e) => handleMinChange(Number(e.target.value))}
          onMouseUp={() => commit(local)}
          onTouchEnd={() => commit(local)}
          onKeyUp={() => commit(local)}
          className="range-thumb absolute w-full h-11 m-0"
        />
        <input
          type="range"
          aria-label="Idade máxima em dias"
          min={boundsMin}
          max={boundsMax}
          value={hi}
          onChange={(e) => handleMaxChange(Number(e.target.value))}
          onMouseUp={() => commit(local)}
          onTouchEnd={() => commit(local)}
          onKeyUp={() => commit(local)}
          className="range-thumb absolute w-full h-11 m-0"
        />
      </div>

      {!emIntervaloCompleto && excluidasSemIdade > 0 && (
        <p className="text-xs text-muted">
          {excluidasSemIdade} oportunidade{excluidasSemIdade === 1 ? "" : "s"} em Prospecting sem
          idade conhecida {excluidasSemIdade === 1 ? "ficou" : "ficaram"} fora deste recorte.
        </p>
      )}
    </div>
  );
}
