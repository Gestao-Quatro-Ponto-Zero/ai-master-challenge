'use client';

/**
 * AbacusDashboard — the house dashboard runtime (abacus-viz on Apache ECharts) as a React component.
 * The manifest describes the dashboard (see components/viz/VIZ.md); `data` holds the rows per data key.
 * The runtime and its CSS are static files under /public/abacus-viz and are loaded once, on the client.
 */
import { useEffect, useRef, useState } from 'react';

export type VizRows = Record<string, unknown>[];
/** Rows keyed by the manifest tiles' `data` keys. */
export type VizData = Record<string, VizRows>;
export type VizTile = {
  id: string;
  type: string;
  data: string;
  span?: number;
  title?: string;
  subtitle?: string;
  insight?: string;
  where?: Record<string, unknown>;
  [field: string]: unknown;
};
export type VizFilter = {
  id: string;
  type: 'tabs';
  label: string;
  field: string;
  options: string[];
  default?: string;
  applies_to: string[];
};
export type VizManifest = {
  title: string;
  eyebrow?: string;
  subtitle?: string;
  /** ISO timestamp; optional when the page passes `dataAsOf` (e.g. from `useDashboardData`). */
  data_as_of?: string;
  theme?: 'auto' | 'editorial' | 'journal' | 'midnight';
  sources?: { id: string; label: string }[];
  filters?: VizFilter[];
  colors?: Record<string, string>;
  tiles: VizTile[];
};

type VizHandle = {
  setData: (next: VizData) => void;
  setAsOf: (iso: string) => void;
  rerender: () => void;
  dispose: () => void;
};

declare global {
  interface Window {
    AbacusViz?: {
      mount: (root: HTMLElement, manifest: VizManifest, data: VizData, opts?: { embedded?: boolean }) => VizHandle;
    };
    echarts?: unknown;
  }
}

const KIT_BASE = '/abacus-viz';
const ECHARTS_SRC = '/abacus-viz/echarts.min.js';
const ECHARTS_CDN = 'https://cdn.jsdelivr.net/npm/echarts@6/dist/echarts.min.js';
const FONTS_HREF =
  'https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&family=Barlow+Semi+Condensed:wght@600;700&family=Barlow:wght@400;500;600&display=swap';

const pending = new Map<string, Promise<void>>();

function loadOnce(key: string, create: () => HTMLElement): Promise<void> {
  const existing = pending.get(key);
  if (existing) return existing;
  const p = new Promise<void>((resolve, reject) => {
    const node = create();
    node.addEventListener('load', () => resolve());
    node.addEventListener('error', () => {
      pending.delete(key);
      node.remove();
      reject(new Error(`failed to load ${key}`));
    });
    document.head.appendChild(node);
  });
  pending.set(key, p);
  return p;
}

const loadScript = (src: string) =>
  loadOnce(src, () => {
    const s = document.createElement('script');
    s.src = src;
    s.async = true;
    return s;
  });

const loadStyle = (href: string) =>
  loadOnce(href, () => {
    const l = document.createElement('link');
    l.rel = 'stylesheet';
    l.href = href;
    return l;
  });

async function ensureKit(): Promise<void> {
  // fonts are best-effort; the kit CSS must be applied before mount (the runtime reads its tokens)
  loadStyle(FONTS_HREF).catch(() => undefined);
  await loadStyle(`${KIT_BASE}/abacus-viz.css`);
  if (!window.echarts) await loadScript(ECHARTS_SRC).catch(() => loadScript(ECHARTS_CDN));
  if (!window.AbacusViz) await loadScript(`${KIT_BASE}/abacus-viz.js`);
}

export type AbacusDashboardProps = {
  manifest: VizManifest;
  data: VizData;
  /** ISO timestamp shown as "Data as of"; defaults to manifest.data_as_of. */
  dataAsOf?: string;
  className?: string;
};

export function AbacusDashboard({ manifest, data, dataAsOf, className }: AbacusDashboardProps) {
  const root = useRef<HTMLDivElement>(null);
  const handle = useRef<VizHandle | null>(null);
  const latest = useRef({ data, dataAsOf });
  latest.current = { data, dataAsOf };
  const shown = useRef<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const manifestKey = JSON.stringify(manifest);
  const hasData = Object.keys(data).length > 0;

  useEffect(() => {
    if (!hasData) return;
    let cancelled = false;
    ensureKit()
      .then(() => {
        if (cancelled || !root.current || !window.AbacusViz) return;
        const own = JSON.parse(manifestKey) as VizManifest; // the runtime mutates data_as_of
        if (latest.current.dataAsOf) own.data_as_of = latest.current.dataAsOf;
        const rows = latest.current.data;
        shown.current = Object.fromEntries(Object.keys(rows).map((k) => [k, JSON.stringify(rows[k])]));
        handle.current = window.AbacusViz.mount(root.current, own, { ...rows }, { embedded: true });
      })
      .catch((e: Error) => setError(e.message));
    return () => {
      cancelled = true;
      handle.current?.dispose();
      handle.current = null;
    };
  }, [manifestKey, hasData]);

  // live data: only the keys whose rows actually changed are pushed, so unchanged tiles do not re-animate
  useEffect(() => {
    if (!handle.current) return;
    const changed: VizData = {};
    for (const key of Object.keys(data)) {
      const serialized = JSON.stringify(data[key]);
      if (shown.current[key] !== serialized) {
        shown.current[key] = serialized;
        changed[key] = data[key];
      }
    }
    if (Object.keys(changed).length) handle.current.setData(changed);
  }, [data]);

  useEffect(() => {
    if (dataAsOf) handle.current?.setAsOf(dataAsOf);
  }, [dataAsOf]);

  if (error) return <p className={className}>The dashboard runtime could not be loaded ({error}).</p>;
  return <div ref={root} className={className} />;
}

export type DashboardPayload = { data: VizData; data_as_of?: string };

/**
 * Polls a JSON route that returns `{ data: { <key>: rows[] }, data_as_of }` and keeps the dashboard live.
 * `refreshMs` 0 fetches once.
 */
export function useDashboardData(url: string, refreshMs = 60_000) {
  const [state, setState] = useState<{ data: VizData; dataAsOf?: string; error?: string }>({ data: {} });
  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const res = await fetch(url, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const payload = (await res.json()) as DashboardPayload;
        if (alive) setState({ data: payload.data, dataAsOf: payload.data_as_of });
      } catch (e) {
        if (alive) setState((s) => ({ ...s, error: e instanceof Error ? e.message : String(e) }));
      }
    };
    tick();
    const id = refreshMs > 0 ? window.setInterval(tick, refreshMs) : undefined;
    return () => {
      alive = false;
      if (id !== undefined) window.clearInterval(id);
    };
  }, [url, refreshMs]);
  return state;
}
