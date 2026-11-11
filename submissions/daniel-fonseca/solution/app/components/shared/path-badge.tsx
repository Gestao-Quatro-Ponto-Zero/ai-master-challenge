import { Bot, UserCheck, Users } from "lucide-react"

import { PATHS } from "@/lib/paths"
import type { PathKey } from "@/lib/types"
import { cn } from "@/lib/utils"

const ICON = { auto: Bot, review: UserCheck, human: Users }

/**
 * Selo do caminho (PRD §5): Resposta automática (verde) · Revisão humana (contorno dourado, sem
 * preenchimento, para não competir com o protagonista) · Somente humano (navy). Rótulo sempre escrito.
 */
export function PathBadge({ path, size = "md", className }: { path: PathKey; size?: "sm" | "md" | "lg"; className?: string }) {
  const Icon = ICON[path]
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border font-semibold",
        size === "sm" && "px-2 py-0.5 text-xs",
        size === "md" && "px-3 py-1 text-sm",
        size === "lg" && "px-4 py-2 text-base",
        path === "auto" && "border-transparent bg-path-auto text-white dark:text-bg",
        path === "review" && "border-path-review bg-transparent text-text-1",
        path === "human" && "border-transparent bg-path-human text-bg",
        className,
      )}
    >
      <Icon className={size === "lg" ? "size-5" : "size-4"} aria-hidden />
      {PATHS[path].label}
    </span>
  )
}
