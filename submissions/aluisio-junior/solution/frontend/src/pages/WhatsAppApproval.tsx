import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { notifyWhatsApp, webhookWhatsApp, fetchOpenRecommendations } from "@/lib/api";
import { useSettings } from "@/contexts/SettingsContext";
import { MetricTooltip } from "@/components/MetricTooltip";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Send, CheckCircle, XCircle, MessageCircle, Info } from "lucide-react";
import { toast } from "sonner";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

interface ApprovalEntry {
  id: string;
  recommendation_id: string;
  target: string;
  status: "queued" | "approved" | "rejected" | "details";
  notes?: string;
}

const statusVariant = (s: string) => {
  switch (s) {
    case "approved": return "default" as const;
    case "rejected": return "destructive" as const;
    case "queued": return "secondary" as const;
    default: return "outline" as const;
  }
};

const statusLabel: Record<string, string> = {
  queued: "Na Fila",
  approved: "Aprovado",
  rejected: "Rejeitado",
  details: "Detalhes Solicitados",
};

const WhatsAppApproval = () => {
  const queryClient = useQueryClient();
  const { cLevels } = useSettings();
  const activeCLevels = cLevels.filter((c) => c.ativo);

  const [entries, setEntries] = useState<ApprovalEntry[]>([]);
  const [selectedRecId, setSelectedRecId] = useState("");
  const [selectedCLevel, setSelectedCLevel] = useState("");
  const [sending, setSending] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Use dedicated open-recommendations endpoint
  const { data: openRecData } = useQuery({
    queryKey: ["open-recommendations"],
    queryFn: fetchOpenRecommendations,
    staleTime: 2 * 60 * 1000,
    retry: 1,
  });

  const openRecommendations = openRecData?.items ?? openRecData ?? [];

  const sendNotification = async () => {
    if (!selectedRecId || !selectedCLevel) return;
    setSending(true);
    try {
      const cLevel = activeCLevels.find((c) => c.id === selectedCLevel);
      await notifyWhatsApp(selectedRecId, cLevel?.nome ?? selectedCLevel);
      const newEntry: ApprovalEntry = {
        id: `${Date.now()}`,
        recommendation_id: selectedRecId,
        target: cLevel?.nome ?? selectedCLevel,
        status: "queued",
      };
      setEntries((prev) => [newEntry, ...prev]);
      setSelectedRecId("");
      toast.success("Notificação enviada via WhatsApp.");
    } catch {
      toast.error("Falha ao enviar notificação.");
    } finally {
      setSending(false);
    }
  };

  const handleAction = async (entry: ApprovalEntry, action: string, notes?: string) => {
    setActionLoading(entry.id);
    try {
      await webhookWhatsApp(action, entry.recommendation_id, notes);
      setEntries((prev) =>
        prev.map((e) =>
          e.id === entry.id ? { ...e, status: action as any, notes } : e
        )
      );
      toast.success(`Ação "${action}" registrada.`);
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["open-recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["kanban-projects"] });
    } catch {
      toast.error("Falha ao registrar ação.");
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      <MetricTooltip tip="Permite enviar recomendações ainda não aprovadas para executivos cadastrados e simular o fluxo de aprovação via WhatsApp.">
        <div className="cursor-default">
          <h1 className="text-2xl font-bold tracking-tight">Aprovação WhatsApp</h1>
          <p className="text-muted-foreground text-sm mt-1">Simulação de fluxo executivo de aprovação</p>
        </div>
      </MetricTooltip>

      {/* Send Notification */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <MessageCircle className="h-4 w-4 text-[hsl(var(--chart-up))]" />
            Enviar Notificação
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-medium">C-Level</label>
              <Select value={selectedCLevel} onValueChange={setSelectedCLevel}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecionar executivo..." />
                </SelectTrigger>
                <SelectContent>
                  {activeCLevels.length === 0 ? (
                    <SelectItem value="__none" disabled>
                      Cadastre executivos em Configurações
                    </SelectItem>
                  ) : (
                    activeCLevels.map((c) => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.nome} — {c.cargo}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1">
              <label className="text-xs text-muted-foreground font-medium">Recomendação</label>
              <Select value={selectedRecId} onValueChange={setSelectedRecId}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecionar recomendação..." />
                </SelectTrigger>
                <SelectContent>
                  {openRecommendations.length === 0 ? (
                    <SelectItem value="__none" disabled>
                      Nenhuma recomendação aberta
                    </SelectItem>
                  ) : (
                    openRecommendations.map((r: any) => (
                      <SelectItem key={r.recommendation_id} value={r.recommendation_id}>
                        {r.recommendation_id} — {r.title}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <Button
                onClick={sendNotification}
                disabled={sending || !selectedRecId || !selectedCLevel}
                className="gap-1.5 w-full"
              >
                {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                Enviar
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Approval Entries */}
      {entries.length === 0 && (
        <div className="flex items-center justify-center h-24 text-muted-foreground text-sm">
          Nenhuma notificação enviada ainda.
        </div>
      )}

      <div className="space-y-3">
        {entries.map((entry) => (
          <Card key={entry.id} className="transition-shadow hover:shadow-md">
            <CardContent className="py-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-mono font-medium">{entry.recommendation_id}</p>
                  <p className="text-xs text-muted-foreground">Enviado para: {entry.target}</p>
                </div>
                <Badge variant={statusVariant(entry.status)} className="text-xs">
                  {statusLabel[entry.status]}
                </Badge>
              </div>

              {entry.notes && (
                <p className="text-xs text-muted-foreground border-l-2 border-border pl-2">{entry.notes}</p>
              )}

              {entry.status === "queued" && (
                <div className="flex gap-2">
                  <Button
                    variant="default"
                    size="sm"
                    className="gap-1 text-xs"
                    disabled={actionLoading === entry.id}
                    onClick={() => handleAction(entry, "approve", "Aprovado pelo CEO")}
                  >
                    <CheckCircle className="h-3.5 w-3.5" /> Aprovar
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    className="gap-1 text-xs"
                    disabled={actionLoading === entry.id}
                    onClick={() => handleAction(entry, "reject", "Rejeitado")}
                  >
                    <XCircle className="h-3.5 w-3.5" /> Rejeitar
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1 text-xs"
                    disabled={actionLoading === entry.id}
                    onClick={() => handleAction(entry, "details", "Mais detalhes solicitados")}
                  >
                    <Info className="h-3.5 w-3.5" /> Detalhes
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default WhatsAppApproval;
