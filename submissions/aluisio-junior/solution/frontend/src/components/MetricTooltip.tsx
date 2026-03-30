import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export function MetricTooltip({ children, tip }: { children: React.ReactNode; tip: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>{children}</TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs text-xs">{tip}</TooltipContent>
    </Tooltip>
  );
}
