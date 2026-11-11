"use client"

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"

/**
 * Pop-up com um documento do projeto (ADR ou judgment log) transcrito do .md.
 * O repositório é privado, então o app mostra o texto completo no lugar do link para o GitHub.
 * O HTML vem do próprio repositório, convertido no build por app/como-foi-feito/_content/generate.mjs.
 */
export function DocDialog({
  eyebrow,
  title,
  html,
  className,
  children,
}: {
  eyebrow: string
  title: string
  html: string
  className?: string
  children: React.ReactNode
}) {
  return (
    <Dialog>
      <DialogTrigger className={className}>{children}</DialogTrigger>
      <DialogContent className="flex max-h-[85vh] flex-col gap-0 overflow-hidden bg-surface p-0 sm:max-w-3xl">
        <DialogHeader className="gap-1.5 border-b border-border px-6 pt-5 pr-14 pb-4">
          <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-text-3">{eyebrow}</p>
          <DialogTitle className="font-serif text-lg leading-snug text-text-1">{title}</DialogTitle>
          <DialogDescription className="sr-only">Documento completo, transcrito do repositório do projeto.</DialogDescription>
        </DialogHeader>
        <div className="doc-prose overflow-y-auto px-6 py-5" dangerouslySetInnerHTML={{ __html: html }} />
      </DialogContent>
    </Dialog>
  )
}
