"use client";

import type { ReactNode } from "react";
import { Chat } from "../Chat";

/** "New chat" clears the transcript — Chat listens for this event. */
function newChat(): void {
  window.dispatchEvent(new CustomEvent("veta:new-chat"));
}

/**
 * The primary surface: the conversation spine. Idle, it shows the executive
 * brief (passed in, server-rendered + grounded); active, the chat transcript.
 */
export function ConversationCanvas({ idleBrief }: { idleBrief: ReactNode }) {
  return (
    <section className="flex min-w-0 flex-1 flex-col rounded-xl border border-edge bg-panel">
      <div className="flex items-center gap-2 border-b border-edge px-4 py-2.5">
        <span className="h-1.5 w-1.5 rounded-full bg-accent" />
        <h2 className="text-[13px] font-semibold text-foreground">Ask Veta</h2>
        <span className="text-[11px] text-faint">grounded · read-only</span>
        <button
          onClick={newChat}
          className="ml-auto inline-flex items-center gap-1 rounded-md border border-edge px-2 py-1 text-[11.5px] text-muted transition-colors hover:border-edge-strong hover:text-foreground"
        >
          New chat
          <span className="text-[13px] leading-none">+</span>
        </button>
      </div>
      <div className="min-h-0 flex-1 p-4">
        <Chat idleBrief={idleBrief} />
      </div>
    </section>
  );
}
