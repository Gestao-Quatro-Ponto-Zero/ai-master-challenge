import { useQuery } from "@tanstack/react-query";
import { fetchChurnRisk } from "@/lib/api";
import { formatCurrency } from "@/lib/formatters";
import { MetricTooltip } from "@/components/MetricTooltip";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, ShieldAlert, Info } from "lucide-react";

interface Account {
  account_id: string;
  mrr: number;
  churn_score: number;
  risk_level: string;
  abc_segment?: string;
}

function getRiskVariant(level: string) {
  const l = level.toLowerCase();
  if (l === "alto" || l === "high") return "destructive" as const;
  if (l === "médio" || l === "medium") return "secondary" as const;
  return "outline" as const;
}

function translateRisk(level: string) {
  const map: Record<string, string> = { High: "Alto", Medium: "Médio", Low: "Baixo" };
  return map[level] ?? level;
}

const ChurnRisk = () => {
  const { data, isLoading, error } = useQuery<Account[]>({
    queryKey: ["churn-risk"],
    queryFn: fetchChurnRisk,
    staleTime: 5 * 60 * 1000,
    select: (raw: any) => {
      const arr: Account[] = Array.isArray(raw) ? raw : raw?.accounts ?? raw?.items ?? [];
      return arr; // use backend ordering
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-destructive text-sm">
        Dados indisponíveis. Verifique se o servidor está ativo.
      </div>
    );
  }

  const accounts = data ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Risco de Churn</h1>
        <p className="text-muted-foreground text-sm mt-1">Contas com maior risco de cancelamento</p>
      </div>

      <div className="glass-card p-4 border-l-4 border-l-destructive bg-destructive/5">
        <p className="text-sm text-foreground font-medium">
          Essas contas devem ser priorizadas para ações de retenção.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-destructive" />
            Contas em Risco
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-muted-foreground">
                  <th className="text-left py-3 px-4 font-medium">#</th>
                  <th className="text-left py-3 px-4 font-medium">Account ID</th>
                  <MetricTooltip tip="Classificação ABC baseada na contribuição de receita da conta.">
                    <th className="text-center py-3 px-4 font-medium cursor-default">
                      Classificação ABC <Info className="h-3 w-3 inline text-muted-foreground" />
                    </th>
                  </MetricTooltip>
                  <MetricTooltip tip="Receita recorrente mensal associada à conta.">
                    <th className="text-right py-3 px-4 font-medium cursor-default">
                      MRR <Info className="h-3 w-3 inline text-muted-foreground" />
                    </th>
                  </MetricTooltip>
                  <MetricTooltip tip="Probabilidade prevista de churn pelo modelo de ML.">
                    <th className="text-right py-3 px-4 font-medium cursor-default">
                      Churn Score <Info className="h-3 w-3 inline text-muted-foreground" />
                    </th>
                  </MetricTooltip>
                  <MetricTooltip tip="Faixa de risco derivada da distribuição do churn score.">
                    <th className="text-center py-3 px-4 font-medium cursor-default">
                      Nível de Risco <Info className="h-3 w-3 inline text-muted-foreground" />
                    </th>
                  </MetricTooltip>
                </tr>
              </thead>
              <tbody>
                {accounts.map((acc, i) => (
                  <tr
                    key={acc.account_id}
                    className={`border-b border-border/50 transition-colors hover:bg-muted/30 ${i < 3 ? "bg-destructive/5" : ""}`}
                  >
                    <td className="py-3 px-4 text-muted-foreground">{i + 1}</td>
                    <td className="py-3 px-4 font-mono text-xs">{acc.account_id}</td>
                    <td className="py-3 px-4 text-center">
                      <Badge variant="outline" className="text-xs font-semibold">
                        {acc.abc_segment ?? "—"}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-right font-medium">{formatCurrency(acc.mrr)}</td>
                    <td className="py-3 px-4 text-right font-semibold">{(acc.churn_score * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4 text-center">
                      <Badge variant={getRiskVariant(acc.risk_level)} className="gap-1">
                        {translateRisk(acc.risk_level)}
                      </Badge>
                    </td>
                  </tr>
                ))}
                {accounts.length === 0 && (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-muted-foreground">
                      Nenhum item disponível
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ChurnRisk;
