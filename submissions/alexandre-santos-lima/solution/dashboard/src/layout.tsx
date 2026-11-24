import { useEffect, useRef, useState } from "react";

export type Pagina = "diagnostico" | "sugestoes" | "dados";
export type Item = { id: string; titulo: string };

export const PAGINAS: { id: Pagina; titulo: string; hash: string }[] = [
  { id: "diagnostico", titulo: "Diagnóstico", hash: "#/" },
  { id: "sugestoes", titulo: "Sugestões", hash: "#/sugestoes" },
  { id: "dados", titulo: "Dados", hash: "#/dados" },
];

const ler = (): Pagina => {
  const h = window.location.hash;
  if (h.startsWith("#/sugestoes")) return "sugestoes";
  if (h.startsWith("#/dados")) return "dados";
  return "diagnostico";
};

/** Rota pela hash (#/, #/sugestoes, #/dados). Âncoras comuns (#secao) mantêm a página atual. */
export function useRota() {
  const [pagina, setPagina] = useState<Pagina>(ler);
  useEffect(() => {
    const on = () => {
      if (!window.location.hash.startsWith("#/")) return;
      setPagina(ler());
      window.scrollTo({ top: 0 });
    };
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return pagina;
}

function useAtiva(itens: Item[]) {
  const [ativa, setAtivaRaw] = useState<string | undefined>(itens[0]?.id);
  const trava = useRef(0); // depois de um clique, a rolagem suave não sobrescreve o item escolhido
  const setAtiva = (id: string | undefined) => { if (Date.now() > trava.current) setAtivaRaw(id); };
  const escolher = (id: string) => { trava.current = Date.now() + 1600; setAtivaRaw(id); };
  useEffect(() => {
    setAtivaRaw(itens[0]?.id);
    // no fim da página a última seção nunca chega ao topo: marca a última
    const fim = () => {
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) setAtiva(itens[itens.length - 1]?.id);
    };
    window.addEventListener("scroll", fim, { passive: true });
    const els = itens.map((i) => document.getElementById(i.id)).filter(Boolean) as HTMLElement[];
    const obs = new IntersectionObserver(
      (es) => {
        const vis = es.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (vis[0] && window.innerHeight + window.scrollY < document.documentElement.scrollHeight - 4) setAtiva(vis[0].target.id);
      },
      { rootMargin: "-80px 0px -60% 0px" },
    );
    els.forEach((e) => obs.observe(e));
    return () => { obs.disconnect(); window.removeEventListener("scroll", fim); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [itens]);
  return [ativa, escolher] as const;
}

const ir = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });

export function Shell({ pagina, itens, isDark, toggle, children }: {
  pagina: Pagina; itens: Item[]; isDark: boolean; toggle: () => void; children: React.ReactNode;
}) {
  const [ativa, setAtiva] = useAtiva(itens);
  const det = useRef<HTMLDetailsElement>(null);
  const clicar = (id: string) => {
    setAtiva(id);
    if (det.current) det.current.open = false;
    ir(id);
  };
  const lista = (
    <ol className="toc-list">
      {itens.map((i, n) => (
        <li key={i.id}>
          <button className={ativa === i.id ? "on" : undefined} aria-current={ativa === i.id ? "true" : undefined} onClick={() => clicar(i.id)}>
            <span className="toc-n">{n + 1}</span>{i.titulo}
          </button>
        </li>
      ))}
    </ol>
  );
  return (
    <>
      <header className="top">
        <div className="bar">
          <span className="brand">RavenStack · Churn</span>
          <nav aria-label="Páginas" className="tabs">
            {PAGINAS.map((p) => (
              <a key={p.id} href={p.hash} aria-current={pagina === p.id ? "page" : undefined}>{p.titulo}</a>
            ))}
          </nav>
          <button className="theme-btn" onClick={toggle} aria-label={isDark ? "Mudar para tema claro" : "Mudar para tema escuro"}>
            {isDark ? "☀ Claro" : "☾ Escuro"}
          </button>
        </div>
      </header>
      <div className="layout">
        <aside className="toc" aria-label="Sumário">
          <div className="toc-title">Sumário</div>
          {lista}
        </aside>
        <details className="toc-mobile" ref={det}>
          <summary>Sumário</summary>
          {lista}
        </details>
        <main className="main">{children}</main>
      </div>
    </>
  );
}
