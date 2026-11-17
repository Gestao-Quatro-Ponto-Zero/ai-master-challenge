"use client";

import { useEffect, useState } from "react";
import { ConversationCanvas } from "../dashboard/ConversationCanvas";

const KEY = "ravenstack:chat-aberto";

/**
 * The analyst chat as a side panel (D27): it opens on any screen without leaving it.
 * The chat stays mounted while closed, so a question fired from anywhere (veta:ask)
 * still lands, and the panel opens to show it.
 */
export function ChatPanel() {
  const [aberto, setAberto] = useState(false);

  useEffect(() => {
    // Restore the last state after mount (localStorage is client-only).
    const salvo = window.localStorage.getItem(KEY) === "1";
    if (salvo) queueMicrotask(() => setAberto(true));
    const abrir = () => setAberto(true);
    window.addEventListener("veta:ask", abrir);
    return () => window.removeEventListener("veta:ask", abrir);
  }, []);

  useEffect(() => {
    window.localStorage.setItem(KEY, aberto ? "1" : "0");
  }, [aberto]);

  return (
    <>
      {!aberto && (
        <button
          onClick={() => setAberto(true)}
          className="fixed right-4 top-[99px] z-30 inline-flex items-center gap-2 rounded-full border border-edge-strong bg-panel px-3 py-1.5 text-[12px] font-medium text-foreground shadow-lg transition-colors hover:border-accent"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-accent" />
          Perguntar ao analista
        </button>
      )}
      <aside
        aria-label="Analista"
        className={`${aberto ? "flex" : "hidden"} h-full w-[440px] shrink-0 flex-col border-l border-edge bg-background p-3`}
      >
        <div className="mb-2 flex items-center justify-between px-1">
          <span className="text-[11px] text-faint">Cada resposta mostra o SQL que rodou.</span>
          <button
            onClick={() => setAberto(false)}
            aria-label="Fechar o analista"
            className="rounded px-2 py-1 text-[12px] text-muted transition-colors hover:text-foreground"
          >
            Fechar ✕
          </button>
        </div>
        <ConversationCanvas
          idleBrief={
            <div className="text-[12.5px] leading-relaxed text-muted">
              Pergunte sobre o que está na tela. Cada resposta mostra a consulta que gerou os números.
            </div>
          }
        />
      </aside>
    </>
  );
}
