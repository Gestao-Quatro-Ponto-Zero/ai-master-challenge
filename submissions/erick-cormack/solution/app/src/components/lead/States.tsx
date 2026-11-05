import { AlertCircle, Inbox } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export function LoadingState({ rows = 6 }: { rows?: number }) {
  return (
    <div className="space-y-2 p-4" aria-busy="true" aria-label="Carregando">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center gap-2 px-4 py-12 text-center text-sm text-muted-foreground">
      <Inbox className="h-6 w-6" />
      {message}
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center gap-2 px-4 py-12 text-center text-sm">
      <AlertCircle className="h-6 w-6 text-destructive" />
      <p className="text-foreground">Não foi possível carregar os dados.</p>
      <p className="text-muted-foreground">{error instanceof Error ? error.message : String(error)}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-2 rounded-md border border-border px-3 py-1.5 hover:bg-muted">
          Tentar de novo
        </button>
      )}
    </div>
  );
}
