import { cn } from "@/lib/utils"

/** Frase-conclusão de uma seção, em serifa. Afirmativa e com o dado (PRD §6.1). */
export function Headline({ children, className }: { children: React.ReactNode; className?: string }) {
  return <h2 className={cn("font-serif text-xl leading-snug text-text-1 sm:text-2xl", className)}>{children}</h2>
}
