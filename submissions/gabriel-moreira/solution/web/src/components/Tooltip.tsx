import { cloneElement, useId, useState, type ReactElement, type ReactNode } from "react";

/** Tooltip da própria aplicação — abre em `mouseenter`/`focus`, fecha em
 * `mouseleave`/`blur`/`Esc`. Substitui o `title` nativo, que demora ~1s
 * para aparecer e não é alcançável por teclado (Requirement "Rótulo e
 * tooltip de confiança", design.md decisão 11). */
export function Tooltip({
  children,
  content,
}: {
  children: ReactElement<{ "aria-describedby"?: string }>;
  content: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const id = useId();

  function close() {
    setOpen(false);
  }

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={close}
      onFocus={() => setOpen(true)}
      onBlur={close}
      onKeyDown={(e) => {
        if (e.key === "Escape") close();
      }}
    >
      {cloneElement(children, { "aria-describedby": open ? id : undefined })}
      {open && (
        <span
          role="tooltip"
          id={id}
          className="absolute z-50 top-full left-1/2 -translate-x-1/2 mt-2 w-64 rounded-xs border border-navy bg-navy text-white text-xs leading-relaxed px-3 py-2 shadow-lg"
        >
          {content}
        </span>
      )}
    </span>
  );
}
