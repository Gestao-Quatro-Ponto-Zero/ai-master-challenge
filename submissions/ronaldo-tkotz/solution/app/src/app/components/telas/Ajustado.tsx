"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

/**
 * Fills the space its parent gives it and hands the exact pixel size to a chart, so the chart's
 * viewBox matches the screen 1:1: text keeps its size in narrow panels, and the chart fills the
 * height instead of setting it. The chart sits absolutely inside, so it can never grow the box.
 */
export function Ajustado({ children, minHeight = 80 }: { children: (largura: number, altura: number) => ReactNode; minHeight?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [caixa, setCaixa] = useState<{ w: number; h: number } | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const medir = () => {
      const w = Math.floor(el.clientWidth);
      const h = Math.floor(el.clientHeight);
      setCaixa((c) => (c && c.w === w && c.h === h ? c : { w, h }));
    };
    medir();
    const ro = new ResizeObserver(medir);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div ref={ref} className="relative min-h-0 flex-1" style={{ minHeight }}>
      {caixa && caixa.w > 0 && caixa.h > 0 && <div className="absolute inset-0">{children(caixa.w, caixa.h)}</div>}
    </div>
  );
}
