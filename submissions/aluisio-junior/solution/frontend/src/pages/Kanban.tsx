import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchKanbanProjects, moveKanbanProject, deleteKanbanProject } from "@/lib/api";
import { MetricTooltip } from "@/components/MetricTooltip";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, User, Users2, Calendar, Target, Trash2 } from "lucide-react";
import { toast } from "sonner";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const stageLabels: Record<string, string> = {
  backlog: "Backlog",
  approved: "Aprovado",
  discovery: "Discovery",
  development: "Desenvolvimento",
  testing: "Testes",
  "go-live": "Go-live",
  monitoring: "Monitoramento",
  done: "Concluído",
};

const stageColors: Record<string, string> = {
  backlog: "bg-muted",
  approved: "bg-primary/10",
  discovery: "bg-[hsl(var(--chart-warning))]/10",
  development: "bg-[hsl(var(--chart-up))]/10",
  testing: "bg-accent/10",
  "go-live": "bg-primary/10",
  monitoring: "bg-secondary",
  done: "bg-[hsl(var(--chart-up))]/20",
};

const priorityVariant = (p: string) => {
  switch (p?.toLowerCase()) {
    case "high": return "destructive" as const;
    case "medium": return "secondary" as const;
    default: return "outline" as const;
  }
};

const Kanban = () => {
  const queryClient = useQueryClient();
  const [deleteTarget, setDeleteTarget] = useState<{ projectId: string; title: string } | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["kanban-projects"],
    queryFn: fetchKanbanProjects,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  const moveMutation = useMutation({
    mutationFn: ({ projectId, newStage }: { projectId: string; newStage: string }) =>
      moveKanbanProject(projectId, newStage),
    onSuccess: () => {
      toast.success("Projeto movido com sucesso.");
      queryClient.invalidateQueries({ queryKey: ["kanban-projects"] });
    },
    onError: () => toast.error("Falha ao mover projeto."),
  });

  const deleteMutation = useMutation({
    mutationFn: (projectId: string) => deleteKanbanProject(projectId),
    onSuccess: () => {
      toast.success("Projeto excluído do Kanban.");
      queryClient.invalidateQueries({ queryKey: ["kanban-projects"] });
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["open-recommendations"] });
    },
    onError: () => toast.error("Falha ao excluir projeto."),
  });

  const handleConfirmDelete = () => {
    if (deleteTarget) {
      deleteMutation.mutate(deleteTarget.projectId);
      setDeleteTarget(null);
    }
  };

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

  const items = data?.items ?? [];
  const stages = data?.stages ?? Object.keys(stageLabels);

  return (
    <div className="space-y-6">
      <MetricTooltip tip="Iniciativas executivas aprovadas acompanhadas em estágios ágeis de entrega.">
        <div className="cursor-default">
          <h1 className="text-2xl font-bold tracking-tight">Kanban</h1>
          <p className="text-muted-foreground text-sm mt-1">Iniciativas executivas em execução ágil</p>
        </div>
      </MetricTooltip>

      {items.length === 0 && (
        <div className="flex items-center justify-center h-32 text-muted-foreground text-sm">
          Nenhum item disponível
        </div>
      )}

      <div className="flex gap-4 overflow-x-auto pb-4">
        {stages.map((stage: string) => {
          const stageItems = items.filter((item: any) => item.current_stage === stage);
          return (
            <div key={stage} className="min-w-[280px] max-w-[320px] flex-shrink-0 space-y-3">
              <div className="flex items-center gap-2">
                <h3 className="text-xs font-semibold uppercase tracking-wider">{stageLabels[stage] ?? stage}</h3>
                <Badge variant="outline" className="text-[10px] h-5">{stageItems.length}</Badge>
              </div>

              <div className={`rounded-lg p-2 min-h-[200px] ${stageColors[stage] ?? "bg-muted"} space-y-2`}>
                {stageItems.map((item: any) => (
                  <Card key={item.project_id} className="shadow-sm">
                    <CardContent className="p-3 space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-xs font-semibold leading-snug">{item.title}</p>
                        <Badge variant={priorityVariant(item.priority)} className="text-[10px] shrink-0">
                          {item.priority}
                        </Badge>
                      </div>

                      {item.description && (
                        <p className="text-[10px] text-muted-foreground line-clamp-2">{item.description}</p>
                      )}

                      <div className="flex flex-wrap gap-2 text-[10px] text-muted-foreground">
                        {item.owner && (
                          <span className="flex items-center gap-0.5">
                            <User className="h-2.5 w-2.5" /> {item.owner}
                          </span>
                        )}
                        {item.squad && (
                          <span className="flex items-center gap-0.5">
                            <Users2 className="h-2.5 w-2.5" /> {item.squad}
                          </span>
                        )}
                        {item.scrum_master && (
                          <span className="flex items-center gap-0.5">
                            <User className="h-2.5 w-2.5" /> SM: {item.scrum_master}
                          </span>
                        )}
                        {item.sprint && (
                          <span className="flex items-center gap-0.5">
                            <Calendar className="h-2.5 w-2.5" /> {item.sprint}
                          </span>
                        )}
                      </div>

                      {item.expected_impact && (
                        <div className="flex items-center gap-1 text-[10px] text-primary">
                          <Target className="h-2.5 w-2.5" />
                          <span>{item.expected_impact}</span>
                        </div>
                      )}

                      <div className="flex gap-2">
                        <Select
                          onValueChange={(newStage) => moveMutation.mutate({ projectId: item.project_id, newStage })}
                        >
                          <SelectTrigger className="h-7 text-[10px] flex-1">
                            <SelectValue placeholder="Mover para..." />
                          </SelectTrigger>
                          <SelectContent>
                            {stages.filter((s: string) => s !== stage).map((s: string) => (
                              <SelectItem key={s} value={s} className="text-xs">
                                {stageLabels[s] ?? s}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                          onClick={() => setDeleteTarget({ projectId: item.project_id, title: item.title })}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir Projeto</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir este projeto do Kanban?
              {deleteTarget && <span className="block mt-1 font-medium text-foreground">"{deleteTarget.title}"</span>}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Kanban;
