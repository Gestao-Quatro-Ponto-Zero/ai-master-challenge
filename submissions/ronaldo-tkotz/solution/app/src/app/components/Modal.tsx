"use client";

import { useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";

/** A centered modal rendered to document.body, dismissable by backdrop / Esc / button. */
export function Modal({
  title,
  subtitle,
  children,
  onClose,
  width = "max-w-5xl",
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  onClose: () => void;
  width?: string;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (typeof document === "undefined") return null;
  return createPortal(
    <div
      className="veta-rise fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className={`flex max-h-[85vh] w-full ${width} flex-col overflow-hidden rounded-xl border border-edge-strong bg-panel shadow-2xl`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex shrink-0 items-center justify-between gap-4 border-b border-edge px-4 py-3">
          <div>
            <h3 className="text-[13px] font-semibold text-foreground">{title}</h3>
            {subtitle && <p className="mt-0.5 text-[11px] text-faint">{subtitle}</p>}
          </div>
          <button onClick={onClose} className="shrink-0 rounded-md px-2 py-1 text-[13px] text-faint hover:bg-surface hover:text-foreground">
            Close ✕
          </button>
        </div>
        <div className="overflow-auto">{children}</div>
      </div>
    </div>,
    document.body,
  );
}
