import type { Queue } from "@/lib/types";

const QUEUE_CLASS: Record<Queue, string> = {
  "Foco agora": "focus",
  Acelerar: "accelerate",
  Nutrir: "nurture",
  "Resgatar ou desqualificar": "rescue",
  Qualificar: "qualify",
};

export function QueueBadge({ queue, compact = false }: { queue: Queue; compact?: boolean }) {
  return (
    <span className={`queue-badge ${QUEUE_CLASS[queue]}${compact ? " compact" : ""}`}>
      <span aria-hidden="true" />
      {queue}
    </span>
  );
}

export function queueClass(queue: Queue): string {
  return QUEUE_CLASS[queue];
}
