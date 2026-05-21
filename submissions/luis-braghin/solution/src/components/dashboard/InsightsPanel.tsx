import { ReactNode, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles, ChevronLeft, ChevronRight } from "lucide-react";

interface InsightsPanelProps {
  title?: string;
  insights: (string | ReactNode)[];
  pageSize?: number;
}

export function InsightsPanel({ title = "Insights IA", insights, pageSize = 8 }: InsightsPanelProps) {
  const [page, setPage] = useState(0);
  const totalPages = Math.ceil(insights.length / pageSize);
  const paged = insights.slice(page * pageSize, (page + 1) * pageSize);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <Sparkles className="h-4 w-4 text-primary" />
            {title}
          </CardTitle>
          {totalPages > 1 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">
                {page + 1} de {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="p-1 rounded-md border border-border text-muted-foreground hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page === totalPages - 1}
                className="p-1 rounded-md border border-border text-muted-foreground hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {paged.map((insight, i) => (
          <div key={page * pageSize + i} className="flex items-start gap-2 rounded-md bg-muted/50 p-3">
            <div className="mt-1 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
            <div className="text-sm text-muted-foreground">{insight}</div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
