import React, { useState, useEffect } from "react";
import type { Lead } from "@/lib/types";
import { useData } from "@/context/DataContext";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { ScoreBadge, ActionBadge, IncompleteBadge } from "./ScoreBadge";
import { AlertTriangle, Save } from "lucide-react";

interface LeadDrawerProps {
  lead: Lead | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function LeadDrawer({ lead, open, onOpenChange }: LeadDrawerProps) {
  const { updateLead } = useData();
  const [sector, setSector] = useState("");
  const [employees, setEmployees] = useState("");

  useEffect(() => {
    if (lead) {
      setSector(lead.sector ?? "");
      setEmployees(lead.employees !== null ? String(lead.employees) : "");
    }
  }, [lead]);

  if (!lead) return null;

  const handleSave = () => {
    const empNum = employees.trim() ? Number(employees) : undefined;
    updateLead(lead.opportunity_id, {
      sector: sector.trim() || undefined,
      employees: empNum !== undefined && !isNaN(empNum) ? empNum : undefined,
    });
    onOpenChange(false);
  };

  const hasMissing = lead.isIncomplete;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[420px] sm:w-[480px] overflow-y-auto">
        <SheetHeader className="mb-6">
          <SheetTitle className="text-lg">{lead.account} — {lead.product}</SheetTitle>
          <SheetDescription>ID: {lead.opportunity_id}</SheetDescription>
        </SheetHeader>

        {/* Badges */}
        <div className="flex flex-wrap gap-1.5 mb-5">
          {!lead.isIncomplete && <ScoreBadge grade={lead.scoreGrade} />}
          <ActionBadge status={lead.actionStatus} />
          {lead.isIncomplete && <IncompleteBadge missingFields={lead.missingFields} />}
        </div>

        {/* Score explanation */}
        {lead.scoreExplanation && (
          <p className="text-xs text-muted-foreground italic mb-5 leading-relaxed">
            {lead.scoreExplanation}
          </p>
        )}

        {/* Metadata */}
        <div className="grid grid-cols-2 gap-3 text-sm mb-6">
          <div>
            <p className="text-[11px] text-muted-foreground uppercase tracking-wide">Vendedor</p>
            <p className="font-medium text-foreground">{lead.sales_agent}</p>
          </div>
          <div>
            <p className="text-[11px] text-muted-foreground uppercase tracking-wide">Manager</p>
            <p className="font-medium text-foreground">{lead.manager}</p>
          </div>
          <div>
            <p className="text-[11px] text-muted-foreground uppercase tracking-wide">Etapa</p>
            <p className="font-medium text-foreground">{lead.deal_stage}</p>
          </div>
          <div>
            <p className="text-[11px] text-muted-foreground uppercase tracking-wide">Porte</p>
            <p className="font-medium text-foreground">{lead.employeeBucket ?? "—"}</p>
          </div>
          <div>
            <p className="text-[11px] text-muted-foreground uppercase tracking-wide">Valor</p>
            <p className="font-medium text-foreground">{lead.close_value > 0 ? `R$ ${lead.close_value.toLocaleString("pt-BR")}` : "—"}</p>
          </div>
          {lead.scoreNumeric !== null && (
            <div>
              <p className="text-[11px] text-muted-foreground uppercase tracking-wide">Score Numérico</p>
              <p className="font-medium text-foreground">{lead.scoreNumeric.toFixed(1)}</p>
            </div>
          )}
        </div>

        {/* Editable fields */}
        <div className="border-t border-border pt-5 space-y-4">
          <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
            {hasMissing && <AlertTriangle className="w-4 h-4 text-[hsl(var(--action-fix))]" />}
            Editar dados do lead
          </h3>

          <div className="space-y-1.5">
            <Label htmlFor="sector" className="text-xs">
              Setor {lead.missingFields.includes("setor") && (
                <span className="text-destructive font-semibold ml-1">— obrigatório</span>
              )}
            </Label>
            <Input
              id="sector"
              value={sector}
              onChange={e => setSector(e.target.value)}
              placeholder="Ex: Technology, Healthcare..."
              className={`h-9 text-sm ${lead.missingFields.includes("setor") ? "border-destructive/50 focus-visible:ring-destructive/30" : ""}`}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="employees" className="text-xs">
              Nº de Funcionários {lead.missingFields.includes("porte") && (
                <span className="text-destructive font-semibold ml-1">— obrigatório</span>
              )}
            </Label>
            <Input
              id="employees"
              type="number"
              value={employees}
              onChange={e => setEmployees(e.target.value)}
              placeholder="Ex: 500"
              className={`h-9 text-sm ${lead.missingFields.includes("porte") ? "border-destructive/50 focus-visible:ring-destructive/30" : ""}`}
            />
          </div>

          <Button onClick={handleSave} className="w-full gap-2">
            <Save className="w-4 h-4" />
            Salvar e recalcular
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
