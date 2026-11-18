"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Minimal sparkline — pure SVG, no axes, no chrome. The whole point is data-ink:
 * show the shape of a grounded series inside a KPI card without stealing focus.
 * Line/area for trends, bars for a discrete monthly schedule (the renewal cliff).
 *
 * Responsive by measurement: it fills the width its KPI card gives it (a ResizeObserver
 * tracks the container) and draws in real pixels, so the trend grows with the card on a
 * wide monitor instead of staying a fixed 92px stub. Height stays fixed — sparklines are
 * meant to be wide-and-short. `width` is only the pre-measure SSR fallback.
 */
export function Sparkline({
  values,
  color = "#8a90ad",
  width = 92,
  height = 26,
  mode = "line",
}: {
  values: number[];
  color?: string;
  width?: number;
  height?: number;
  mode?: "line" | "bar";
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [w, setW] = useState(width);

  useEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver((entries) => {
      const cw = entries[0]?.contentRect.width;
      if (cw && cw > 0) setW(cw);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  if (!values || values.length < 2) {
    return <div ref={ref} className="w-full" style={{ height }} aria-hidden />;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const pad = 2;
  const h = height - pad * 2;

  let body: React.ReactNode;
  if (mode === "bar") {
    const gap = 2;
    const bw = (w - gap * (values.length - 1)) / values.length;
    body = values.map((v, i) => {
      const bh = Math.max(1.5, ((v - min) / span) * h);
      const x = i * (bw + gap);
      const isLast = i === values.length - 1;
      return <rect key={i} x={x} y={height - pad - bh} width={Math.max(0.5, bw)} height={bh} rx={1} fill={color} opacity={isLast ? 1 : 0.45} />;
    });
  } else {
    const stepX = w / (values.length - 1);
    const pts = values.map((v, i) => [i * stepX, pad + h - ((v - min) / span) * h] as const);
    const line = pts.map((pt, i) => `${i === 0 ? "M" : "L"}${pt[0].toFixed(1)} ${pt[1].toFixed(1)}`).join(" ");
    const area = `${line} L ${w.toFixed(1)} ${height} L 0 ${height} Z`;
    const last = pts[pts.length - 1];
    body = (
      <>
        <path d={area} fill={color} opacity={0.12} />
        <path d={line} fill="none" stroke={color} strokeWidth={1.5} strokeLinejoin="round" strokeLinecap="round" />
        <circle cx={last[0]} cy={last[1]} r={2} fill={color} />
      </>
    );
  }

  return (
    <div ref={ref} className="w-full">
      <svg width={w} height={height} viewBox={`0 0 ${w} ${height}`} className="block overflow-visible" aria-hidden>
        {body}
      </svg>
    </div>
  );
}
